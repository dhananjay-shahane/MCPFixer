import os
import sys
from typing import Dict, Any
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json
import numpy as np
import subprocess

class DirectClient:
    """Direct client that executes MCP tools without the protocol overhead"""
    
    def __init__(self):
        """Initialize the client with available tools"""
        self.available_tools = {}
        self._setup_tools()
    
    def _setup_tools(self):
        """Set up the available tools by defining them directly"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs("output", exist_ok=True)
            os.makedirs("data", exist_ok=True)
            
            # Define tool functions directly to avoid MCP wrapper issues
            def read_csv(filename: str):
                try:
                    filepath = f"data/{filename}"
                    if os.path.exists(filepath):
                        df = pd.read_csv(filepath)
                        return df.to_string(index=False)
                    else:
                        return f"File {filename} not found in data directory"
                except Exception as e:
                    return f"Error reading CSV file: {str(e)}"
            
            def get_data_stats(data_source: str):
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
                    
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        stats["numeric_statistics"] = df[numeric_cols].describe().to_dict()
                    
                    categorical_cols = df.select_dtypes(include=['object']).columns
                    categorical_stats = {}
                    for col in categorical_cols:
                        if df[col].nunique() <= 20:
                            categorical_stats[col] = df[col].value_counts().to_dict()
                    
                    if categorical_stats:
                        stats["categorical_statistics"] = categorical_stats
                    
                    return json.dumps(stats, indent=2, default=str)
                except Exception as e:
                    return f"Error getting stats: {str(e)}"
            
            def generate_chart(data_source: str, chart_type: str = 'bar', title: str = 'Chart', x_axis: str = 'x', y_axis: str = 'y'):
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
            
            def filter_data(data_source: str, column: str, value: str, operation: str = "equals"):
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
                        "data": filtered.head(100).to_string(index=False)
                    }
                    
                    return json.dumps(result, indent=2)
                except Exception as e:
                    return f"Error filtering data: {str(e)}"
            
            def get_column_info(data_source: str, column: str = None):
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
                        
                        if pd.api.types.is_numeric_dtype(df[col]):
                            info.update({
                                "min": float(df[col].min()) if not df[col].isnull().all() else None,
                                "max": float(df[col].max()) if not df[col].isnull().all() else None,
                                "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                                "median": float(df[col].median()) if not df[col].isnull().all() else None,
                                "std": float(df[col].std()) if not df[col].isnull().all() else None
                            })
                        else:
                            if df[col].nunique() <= 10:
                                info["top_values"] = df[col].value_counts().head(10).to_dict()
                            else:
                                info["sample_values"] = df[col].dropna().head(5).tolist()
                        
                        column_info[col] = info
                    
                    return json.dumps(column_info, indent=2, default=str)
                except Exception as e:
                    return f"Error getting column info: {str(e)}"
            
            def list_data_files():
                try:
                    data_dir = "data"
                    if not os.path.exists(data_dir):
                        return "Data directory not found"
                    
                    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
                    return json.dumps({"available_files": csv_files}, indent=2)
                except Exception as e:
                    return f"Error listing files: {str(e)}"
            
            def execute_script(script_name: str, csv_file: str, args: str = ""):
                try:
                    script_path = f"scripts/{script_name}"
                    if not os.path.exists(script_path):
                        available_scripts = [f for f in os.listdir("scripts") if f.endswith('.py')]
                        return f"Script {script_name} not found. Available scripts: {available_scripts}"
                    
                    csv_path = f"data/{csv_file}"
                    if not os.path.exists(csv_path):
                        return f"CSV file {csv_file} not found in data directory"
                    
                    cmd = [sys.executable, script_path, csv_path]
                    if args:
                        cmd.extend(args.split())
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
                    
                    if result.returncode == 0:
                        return f"Script executed successfully:\n{result.stdout}"
                    else:
                        return f"Script execution failed:\n{result.stderr}"
                except Exception as e:
                    return f"Error executing script: {str(e)}"
            
            # Map tool names to functions
            self.available_tools = {
                "read_csv": read_csv,
                "generate_chart": generate_chart,
                "get_data_stats": get_data_stats,
                "filter_data": filter_data,
                "get_column_info": get_column_info,
                "list_data_files": list_data_files,
                "execute_script": execute_script
            }
                    
        except Exception as e:
            print(f"Error setting up direct client: {e}")
            self.available_tools = {}
    
    def list_tools(self) -> Dict[str, str]:
        """Get a list of available tools with descriptions"""
        return {
            "read_csv": "Read CSV file content from data directory",
            "get_data_stats": "Get comprehensive statistics about CSV data", 
            "get_column_info": "Get detailed information about columns in dataset",
            "filter_data": "Filter CSV data by column value with various operations",
            "generate_chart": "Generate charts from CSV data (bar, line, scatter, pie)",
            "list_data_files": "List all available CSV files in the data directory",
            "execute_script": "Execute analysis scripts (bar_chart_generator.py, pie_chart_generator.py, data_analyzer.py)"
        }
    
    def list_resources(self) -> Dict[str, str]:
        """Get a list of available resources"""
        return {
            "csv://{filename}": "Access CSV file content as a resource"
        }
    
    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific tool"""
        tool_info = {
            "read_csv": {
                "description": "Read CSV file content from data directory",
                "parameters": {
                    "filename": "Name of the CSV file in the data directory"
                },
                "example": {"filename": "sample_data.csv"}
            },
            "get_data_stats": {
                "description": "Get comprehensive statistics about CSV data",
                "parameters": {
                    "data_source": "Name of the CSV file in the data directory"
                },
                "example": {"data_source": "sample_data.csv"}
            },
            "get_column_info": {
                "description": "Get detailed information about columns in dataset",
                "parameters": {
                    "data_source": "Name of the CSV file in the data directory",
                    "column": "Specific column name (optional)"
                },
                "example": {"data_source": "sample_data.csv", "column": "age"}
            },
            "filter_data": {
                "description": "Filter CSV data by column value with various operations",
                "parameters": {
                    "data_source": "Name of the CSV file in the data directory",
                    "column": "Column name to filter by",
                    "value": "Value to filter for",
                    "operation": "Filter operation (equals, contains, greater, less, not_equals)"
                },
                "example": {"data_source": "sample_data.csv", "column": "age", "value": "25", "operation": "greater"}
            },
            "generate_chart": {
                "description": "Generate charts from CSV data",
                "parameters": {
                    "data_source": "Name of the CSV file in the data directory",
                    "chart_type": "Type of chart (bar, line, scatter, pie)",
                    "title": "Chart title",
                    "x_axis": "Column name for x-axis",
                    "y_axis": "Column name for y-axis"
                },
                "example": {"data_source": "sample_data.csv", "chart_type": "bar", "title": "Age Distribution", "x_axis": "name", "y_axis": "age"}
            },
            "list_data_files": {
                "description": "List all available CSV files in the data directory",
                "parameters": {},
                "example": {}
            },
            "execute_script": {
                "description": "Execute analysis scripts with CSV data",
                "parameters": {
                    "script_name": "Script to execute (bar_chart_generator.py, pie_chart_generator.py, data_analyzer.py)",
                    "csv_file": "CSV file to process",
                    "args": "Additional arguments as string (optional)"
                },
                "example": {"script_name": "bar_chart_generator.py", "csv_file": "sales_data.csv", "args": "Product Sales"}
            }
        }
        return tool_info.get(tool_name)
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Execute a tool directly with given parameters"""
        if not self.available_tools:
            return "Error: No tools available. Server functions could not be imported."
            
        if tool_name not in self.available_tools:
            available = ", ".join(self.available_tools.keys())
            return f"Unknown tool: {tool_name}. Available tools: {available}"
        
        try:
            # Call the function with the provided parameters
            result = self.available_tools[tool_name](**params)
            return str(result)
        except TypeError as e:
            tool_info = self.get_tool_info(tool_name)
            if tool_info:
                expected_params = tool_info.get("parameters", {})
                example = tool_info.get("example", {})
                return f"Parameter error for {tool_name}: {str(e)}\nExpected parameters: {expected_params}\nExample: {example}"
            return f"Parameter error for {tool_name}: {str(e)}"
        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"
    
    def validate_data_file(self, filename: str) -> bool:
        """Check if a data file exists"""
        return os.path.exists(f"data/{filename}")
    
    def list_data_files(self) -> list:
        """List all CSV files in the data directory"""
        data_dir = "data"
        if not os.path.exists(data_dir):
            return []
        
        csv_files = []
        for file in os.listdir(data_dir):
            if file.endswith('.csv'):
                csv_files.append(file)
        return csv_files

def main():
    """Interactive command line interface for direct client"""
    client = DirectClient()
    
    print("MCP Data Analysis - Direct Client")
    print("=" * 40)
    print("Available commands:")
    print("  tools - List available tools")
    print("  info <tool_name> - Get tool information")
    print("  files - List data files")
    print("  exec <tool_name> <params_json> - Execute tool")
    print("  help - Show this help")
    print("  quit - Exit")
    print()
    
    # Show available data files
    data_files = client.list_data_files()
    if data_files:
        print(f"Available data files: {', '.join(data_files)}")
    else:
        print("No CSV files found in data directory")
    print()
    
    while True:
        try:
            user_input = input("direct_client> ").strip().split()
            if not user_input:
                continue
                
            command = user_input[0].lower()
            
            if command == "quit":
                break
            elif command == "tools":
                tools = client.list_tools()
                for name, desc in tools.items():
                    print(f"  {name}: {desc}")
            elif command == "files":
                files = client.list_data_files()
                if files:
                    print("Available CSV files:")
                    for file in files:
                        print(f"  - {file}")
                else:
                    print("No CSV files found")
            elif command == "info" and len(user_input) > 1:
                tool_name = user_input[1]
                info = client.get_tool_info(tool_name)
                if info:
                    print(f"Tool: {tool_name}")
                    print(f"Description: {info['description']}")
                    print(f"Parameters: {info['parameters']}")
                    print(f"Example: {info['example']}")
                else:
                    print(f"Tool '{tool_name}' not found")
            elif command == "exec" and len(user_input) > 2:
                tool_name = user_input[1]
                try:
                    params = json.loads(' '.join(user_input[2:]))
                    result = client.execute_tool(tool_name, params)
                    print(result)
                except json.JSONDecodeError:
                    print("Invalid JSON parameters")
            elif command == "help":
                print("Available commands:")
                print("  tools - List available tools")
                print("  info <tool_name> - Get tool information") 
                print("  files - List data files")
                print("  exec <tool_name> <params_json> - Execute tool")
                print("  help - Show this help")
                print("  quit - Exit")
            else:
                print(f"Unknown command: {command}. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("Goodbye!")

if __name__ == "__main__":
    main()