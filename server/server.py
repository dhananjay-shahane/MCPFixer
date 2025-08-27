import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import json
import sys
from fastmcp import FastMCP
import numpy as np
import subprocess

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)
os.makedirs("data", exist_ok=True)

mcp = FastMCP("Data Analysis Server")

@mcp.resource("csv://{filename}")
def read_csv_resource(filename: str):
    """Read CSV file from data directory as a resource"""
    filepath = f"data/{filename}"
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return f.read()
    return None

@mcp.tool()
def read_csv(filename: str):
    """Read CSV file from data directory"""
    try:
        filepath = f"data/{filename}"
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            return df.to_string(index=False)
        else:
            return f"File {filename} not found in data directory"
    except Exception as e:
        return f"Error reading CSV file: {str(e)}"

@mcp.tool()
def generate_chart(
    data_source: str,
    chart_type: str = 'bar',
    title: str = 'Chart',
    x_axis: str = 'x',
    y_axis: str = 'y'
):
    """Generate charts from CSV data
    
    Args:
        data_source: Name of the CSV file in the data directory
        chart_type: Type of chart ('bar', 'line', 'scatter', 'pie')
        title: Chart title
        x_axis: Column name for x-axis
        y_axis: Column name for y-axis
    """
    try:
        filepath = f'data/{data_source}'
        if not os.path.exists(filepath):
            return f"Data file {data_source} not found in data directory"
            
        df = pd.read_csv(filepath)
        
        if x_axis not in df.columns:
            return f"Column '{x_axis}' not found in data. Available columns: {list(df.columns)}"
        
        if y_axis not in df.columns and chart_type != 'pie':
            return f"Column '{y_axis}' not found in data. Available columns: {list(df.columns)}"
        
        plt.figure(figsize=(12, 8))
        
        if chart_type == 'bar':
            plt.bar(df[x_axis], df[y_axis])
            plt.xlabel(x_axis)
            plt.ylabel(y_axis)
        elif chart_type == 'line':
            plt.plot(df[x_axis], df[y_axis], marker='o')
            plt.xlabel(x_axis)
            plt.ylabel(y_axis)
        elif chart_type == 'scatter':
            plt.scatter(df[x_axis], df[y_axis])
            plt.xlabel(x_axis)
            plt.ylabel(y_axis)
        elif chart_type == 'pie':
            # Group by x_axis and sum y_axis values
            grouped_data = df.groupby(x_axis)[y_axis].sum() if y_axis in df.columns else df[x_axis].value_counts()
            plt.pie(grouped_data.values, labels=grouped_data.index, autopct='%1.1f%%')
        else:
            return f"Unsupported chart type: {chart_type}. Supported types: bar, line, scatter, pie"
        
        plt.title(title)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/chart_{chart_type}_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"Chart saved as {filename}"
        
    except Exception as e:
        return f"Error generating chart: {str(e)}"

@mcp.tool()
def get_data_stats(data_source: str):
    """Get comprehensive statistics about CSV data
    
    Args:
        data_source: Name of the CSV file in the data directory
    """
    try:
        filepath = f'data/{data_source}'
        if not os.path.exists(filepath):
            return f"Data file {data_source} not found in data directory"
            
        df = pd.read_csv(filepath)
        
        stats = {
            "file_info": {
                "filename": data_source,
                "shape": df.shape,
                "size_mb": round(os.path.getsize(filepath) / (1024*1024), 4)
            },
            "columns": list(df.columns),
            "data_types": df.dtypes.astype(str).to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "null_percentages": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
        }
        
        # Add descriptive statistics for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            stats["numeric_statistics"] = df[numeric_cols].describe().to_dict()
        
        # Add value counts for categorical columns (if not too many unique values)
        categorical_cols = df.select_dtypes(include=['object']).columns
        categorical_stats = {}
        for col in categorical_cols:
            if df[col].nunique() <= 20:  # Only for columns with <= 20 unique values
                categorical_stats[col] = df[col].value_counts().to_dict()
        
        if categorical_stats:
            stats["categorical_statistics"] = categorical_stats
        
        return json.dumps(stats, indent=2, default=str)
        
    except Exception as e:
        return f"Error getting stats: {str(e)}"

@mcp.tool()
def filter_data(data_source: str, column: str, value: str, operation: str = "equals"):
    """Filter CSV data by column value with various operations
    
    Args:
        data_source: Name of the CSV file in the data directory
        column: Column name to filter by
        value: Value to filter for
        operation: Filter operation ('equals', 'contains', 'greater', 'less', 'not_equals')
    """
    try:
        filepath = f'data/{data_source}'
        if not os.path.exists(filepath):
            return f"Data file {data_source} not found in data directory"
            
        df = pd.read_csv(filepath)
        
        if column not in df.columns:
            return f"Column '{column}' not found in data. Available columns: {list(df.columns)}"
        
        # Apply filtering based on operation
        if operation == "equals":
            filtered = df[df[column] == value]
        elif operation == "contains":
            filtered = df[df[column].astype(str).str.contains(str(value), case=False, na=False)]
        elif operation == "greater":
            try:
                filtered = df[pd.to_numeric(df[column], errors='coerce') > float(value)]
            except ValueError:
                return f"Cannot perform 'greater' operation on non-numeric data in column '{column}'"
        elif operation == "less":
            try:
                filtered = df[pd.to_numeric(df[column], errors='coerce') < float(value)]
            except ValueError:
                return f"Cannot perform 'less' operation on non-numeric data in column '{column}'"
        elif operation == "not_equals":
            filtered = df[df[column] != value]
        else:
            return f"Unsupported operation: {operation}. Supported: equals, contains, greater, less, not_equals"
        
        if len(filtered) == 0:
            return f"No rows found matching the filter criteria"
        
        result = {
            "filtered_count": len(filtered),
            "total_count": len(df),
            "percentage": round(len(filtered) / len(df) * 100, 2),
            "data": filtered.head(100).to_string(index=False)  # Limit to first 100 rows
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return f"Error filtering data: {str(e)}"

@mcp.tool()
def get_column_info(data_source: str, column: str = None):
    """Get detailed information about columns in the dataset
    
    Args:
        data_source: Name of the CSV file in the data directory
        column: Specific column name (optional, if not provided, returns info for all columns)
    """
    try:
        filepath = f'data/{data_source}'
        if not os.path.exists(filepath):
            return f"Data file {data_source} not found in data directory"
            
        df = pd.read_csv(filepath)
        
        if column and column not in df.columns:
            return f"Column '{column}' not found in data. Available columns: {list(df.columns)}"
        
        columns_to_analyze = [column] if column else df.columns
        column_info = {}
        
        for col in columns_to_analyze:
            info = {
                "data_type": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "null_percentage": round(df[col].isnull().sum() / len(df) * 100, 2),
                "unique_values": int(df[col].nunique()),
                "memory_usage": int(df[col].memory_usage(deep=True))
            }
            
            # Add statistics based on data type
            if pd.api.types.is_numeric_dtype(df[col]):
                info.update({
                    "min": float(df[col].min()) if not df[col].isnull().all() else None,
                    "max": float(df[col].max()) if not df[col].isnull().all() else None,
                    "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                    "median": float(df[col].median()) if not df[col].isnull().all() else None,
                    "std": float(df[col].std()) if not df[col].isnull().all() else None
                })
            else:
                # For non-numeric columns, show top values
                if df[col].nunique() <= 10:
                    info["top_values"] = df[col].value_counts().head(10).to_dict()
                else:
                    info["sample_values"] = df[col].dropna().head(5).tolist()
            
            column_info[col] = info
        
        return json.dumps(column_info, indent=2, default=str)
        
    except Exception as e:
        return f"Error getting column info: {str(e)}"

@mcp.tool()
def list_data_files():
    """List all available CSV files in the data directory"""
    try:
        data_dir = "data"
        if not os.path.exists(data_dir):
            return "Data directory not found"
        
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        return json.dumps({"available_files": csv_files}, indent=2)
        
    except Exception as e:
        return f"Error listing files: {str(e)}"

@mcp.tool() 
def execute_script(script_name: str, csv_file: str, args: str = ""):
    """Execute a script from the scripts directory with CSV file and arguments
    
    Args:
        script_name: Name of the script to execute (bar_chart_generator.py, pie_chart_generator.py, data_analyzer.py)
        csv_file: CSV file to process
        args: Additional arguments to pass to the script as string
    """
    try:
        script_path = f"scripts/{script_name}"
        if not os.path.exists(script_path):
            available_scripts = [f for f in os.listdir("scripts") if f.endswith('.py')]
            return f"Script {script_name} not found. Available scripts: {available_scripts}"
        
        csv_path = f"data/{csv_file}"
        if not os.path.exists(csv_path):
            return f"CSV file {csv_file} not found in data directory"
        
        # Build command
        cmd = [sys.executable, script_path, csv_path]
        if args:
            cmd.extend(args.split())
        
        # Execute script
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            return f"Script executed successfully:\n{result.stdout}"
        else:
            return f"Script execution failed:\n{result.stderr}"
            
    except Exception as e:
        return f"Error executing script: {str(e)}"

@mcp.prompt()
def analyze_data_prompt(csv_file: str, question: str):
    """Analyze data and provide insights based on user question
    
    Args:
        csv_file: Name of the CSV file to analyze
        question: User's question about the data
    """
    return f"""You are a data analysis assistant. Analyze the CSV file '{csv_file}' and answer this question: {question}

Available tools:
- read_csv: Read the CSV file content
- get_data_stats: Get statistical summary
- get_column_info: Get column details  
- filter_data: Filter data by conditions
- generate_chart: Create visualizations
- execute_script: Run analysis scripts

Provide insights and suggest visualizations that would help answer the question."""

if __name__ == "__main__":
    mcp.run()