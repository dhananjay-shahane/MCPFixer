"""
Flask web application for MCP Data Analysis System
Provides a web interface for data analysis tools
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from pathlib import Path
import sys
import asyncio
import subprocess
from contextlib import AsyncExitStack
from typing import Optional

# MCP imports
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("Warning: MCP client libraries not available. Install with: pip install mcp")
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Initialize Flask app
app = Flask(__name__)

# Simplified MCP client that works directly with the server module
class MCPClient:
    def __init__(self):
        self.mcp_server = None
        self.connected = False
    
    def connect_to_server(self):
        """Connect to MCP server by importing it directly"""
        try:
            from server.server import mcp
            self.mcp_server = mcp
            self.connected = True
            return True
        except Exception as e:
            print(f"Error connecting to MCP server: {e}")
            self.connected = False
            return False
    
    def call_tool(self, tool_name: str, tool_args: dict):
        """Call a tool on the MCP server"""
        if not self.connected:
            if not self.connect_to_server():
                raise RuntimeError("Cannot connect to MCP server")
        
        # Import the actual tool functions directly from the server module
        try:
            import server.server as server_module
            
            # Create a direct mapping to the actual Python functions
            # These are the original functions before FastMCP wrapping
            def read_csv_direct(filename: str):
                import pandas as pd
                import os
                try:
                    filepath = f"data/{filename}"
                    if os.path.exists(filepath):
                        df = pd.read_csv(filepath)
                        return df.to_string(index=False)
                    else:
                        return f"File {filename} not found in data directory"
                except Exception as e:
                    return f"Error reading CSV file: {str(e)}"
            
            def list_data_files_direct():
                import os
                import json
                try:
                    data_dir = "data"
                    if not os.path.exists(data_dir):
                        return json.dumps({"available_files": []}, indent=2)
                    
                    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
                    return json.dumps({"available_files": csv_files}, indent=2)
                    
                except Exception as e:
                    return f"Error listing files: {str(e)}"
            
            def get_data_stats_direct(data_source: str):
                import pandas as pd
                import numpy as np
                import os
                import json
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
                    
                    # Add value counts for categorical columns
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
            
            def generate_chart_direct(data_source: str, chart_type: str = 'bar', title: str = 'Chart', x_axis: str = 'x', y_axis: str = 'y'):
                import pandas as pd
                import matplotlib.pyplot as plt
                from datetime import datetime
                import os
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
            
            def get_column_info_direct(data_source: str, column: str = None):
                import pandas as pd
                import json
                import os
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
            
            def filter_data_direct(data_source: str, column: str, value: str, operation: str = "equals"):
                import pandas as pd
                import json
                import os
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
            
            def execute_script_direct(script_name: str, csv_file: str, args: str = ""):
                import subprocess
                import sys
                import os
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
            
            # Direct function mapping
            direct_functions = {
                "read_csv": read_csv_direct,
                "list_data_files": list_data_files_direct,
                "get_data_stats": get_data_stats_direct,
                "generate_chart": generate_chart_direct,
                "get_column_info": get_column_info_direct,
                "filter_data": filter_data_direct,
                "execute_script": execute_script_direct
            }
            
            if tool_name in direct_functions:
                return direct_functions[tool_name](**tool_args)
            else:
                available_tools = list(direct_functions.keys())
                raise RuntimeError(f"Tool {tool_name} not found. Available tools: {available_tools}")
                
        except ImportError as e:
            raise RuntimeError(f"Cannot import required modules: {e}")
        except Exception as e:
            raise RuntimeError(f"Error calling tool {tool_name}: {e}")
    
    def list_tools(self):
        """List available tools from MCP server"""
        if not self.connected:
            if not self.connect_to_server():
                return []
        
        # Return hardcoded list of available tools
        tools = [
            {"name": "read_csv", "description": "Read CSV file from data directory"},
            {"name": "generate_chart", "description": "Generate charts from CSV data"},
            {"name": "get_data_stats", "description": "Get comprehensive statistics about CSV data"},
            {"name": "filter_data", "description": "Filter CSV data by column value"},
            {"name": "get_column_info", "description": "Get detailed information about columns"},
            {"name": "list_data_files", "description": "List all available CSV files"},
            {"name": "execute_script", "description": "Execute custom analysis scripts"}
        ]
        return tools
    
    def list_resources(self):
        """List available resources from MCP server"""
        if not self.connected:
            if not self.connect_to_server():
                return []
        
        if not self.mcp_server:
            return []
        
        resources = []
        if (hasattr(self.mcp_server, '_resource_manager') and 
            self.mcp_server._resource_manager is not None and 
            hasattr(self.mcp_server._resource_manager, '_resources')):
            for resource_pattern, resource in self.mcp_server._resource_manager._resources.items():
                resources.append({
                    "uri": resource_pattern,
                    "name": resource_pattern,
                    "description": getattr(resource, 'description', f"MCP resource: {resource_pattern}") or f"MCP resource: {resource_pattern}",
                    "mimeType": "text/csv"
                })
        else:
            # Fallback resources
            resources = [
                {
                    "uri": "csv://{filename}",
                    "name": "CSV Files",
                    "description": "Read CSV file content as a resource",
                    "mimeType": "text/csv"
                }
            ]
        return resources

# Global MCP client instance
mcp_client = MCPClient()


# Ensure required directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

@app.route('/')
def index():
    """AI Chat Interface"""
    try:
        # Get available data files
        data_files = []
        if os.path.exists("data"):
            data_files = [f for f in os.listdir("data") if f.endswith('.csv')]
        
        # Get tools and resources using MCP client
        result = get_mcp_info_sync()
        
        import time
        timestamp = int(time.time())
        return render_template('chat.html', 
                             data_files=data_files, 
                             tools=result.get('tools', {}), 
                             resources=result.get('resources', {}), 
                             timestamp=timestamp)
    except Exception as e:
        print(f"ERROR loading chat interface: {str(e)}")
        return f"Error loading chat interface: {str(e)}", 500


def get_mcp_info_sync():
    """Get tools and resources from MCP server (synchronous version)"""
    global mcp_client
    
    try:
        # Connect to MCP server if not already connected
        if not mcp_client.connected:
            mcp_client.connect_to_server()
        
        # Get tools and resources
        tools_list = mcp_client.list_tools()
        resources_list = mcp_client.list_resources()
        
        tools = {tool['name']: tool['description'] for tool in tools_list}
        resources = {resource['uri']: resource['description'] for resource in resources_list}
        
        return {'tools': tools, 'resources': resources}
        
    except Exception as e:
        print(f"Error getting MCP info: {e}")
        return {
            'tools': {'Error': 'Could not connect to MCP server'}, 
            'resources': {'csv://{filename}': 'CSV file resource'}
        }

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process natural language chat queries using MCP client"""
    try:
        data = request.get_json()
        user_query = data.get('message', '')
        tool_name = data.get('tool_name', None)
        tool_params = data.get('tool_params', {})
        
        if not user_query and not tool_name:
            return jsonify({'error': 'Message or tool name is required'}), 400
        
        # Use synchronous function to avoid async issues
        if tool_params is None:
            tool_params = {}
        result = process_query_sync(user_query, tool_name, tool_params)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def process_query_sync(user_query: str, tool_name: str = None, tool_params: dict = None):
    """Process query using MCP client (synchronous version)"""
    global mcp_client
    
    try:
        # Connect to MCP server if not already connected
        if not mcp_client.connected:
            mcp_client.connect_to_server()
        
        tool_result = None
        tool_used = None
        tool_parameters = None
        ai_response = ""
        
        # Direct tool execution if tool_name is provided
        if tool_name:
            try:
                # Use MCP client to call tool
                if tool_name in ["read_csv", "get_data_stats", "generate_chart", 
                               "get_column_info", "filter_data", "list_data_files", "execute_script"]:
                    tool_result = mcp_client.call_tool(tool_name, tool_params)
                    tool_used = tool_name
                    tool_parameters = tool_params
                    ai_response = f"Executed {tool_name} successfully."
                else:
                    ai_response = f"Unknown tool: {tool_name}"
            except Exception as e:
                ai_response = f"Error executing {tool_name}: {str(e)}"
        
        else:
            # Natural language processing with intelligent tool selection
            query_lower = user_query.lower()
            
            # Get available files using MCP client
            available_files = []
            try:
                file_list_result = mcp_client.call_tool("list_data_files", {})
                if file_list_result:
                    files_data = json.loads(file_list_result)
                    available_files = files_data.get('available_files', [])
            except:
                available_files = [f for f in os.listdir('data') if f.endswith('.csv')] if os.path.exists('data') else []
            
            # Smart file detection
            detected_file = None
            for word in user_query.split():
                if word.endswith('.csv') and word in available_files:
                    detected_file = word
                    break
            
            # If no specific file mentioned, try to match patterns
            if not detected_file:
                for file in available_files:
                    file_base = file.replace('_', ' ').replace('.csv', '').lower()
                    if file_base in query_lower or any(part in query_lower for part in file_base.split()):
                        detected_file = file
                        break
            
            # Tool selection based on query intent
            if any(word in query_lower for word in ['read', 'show', 'display', 'view', 'content']):
                if detected_file:
                    tool_result = mcp_client.call_tool("read_csv", {"filename": detected_file})
                    tool_used = "read_csv"
                    tool_parameters = {"filename": detected_file}
                    ai_response = f"Reading {detected_file} from the data directory."
                else:
                    ai_response = f"Please specify which file to read. Available files: {', '.join(available_files)}"
                    
            elif any(word in query_lower for word in ['chart', 'graph', 'plot', 'visualiz']):
                if detected_file:
                    chart_type = 'bar'
                    if 'pie' in query_lower: chart_type = 'pie'
                    elif 'line' in query_lower: chart_type = 'line'
                    elif 'scatter' in query_lower: chart_type = 'scatter'
                    
                    # Get basic column info for defaults
                    try:
                        csv_data = mcp_client.call_tool("read_csv", {"filename": detected_file})
                        # Simple parsing to get column names
                        lines = csv_data.split('\n') if csv_data else []
                        if lines:
                            columns = lines[0].split()
                            x_axis = columns[0] if columns else 'x'
                            y_axis = columns[1] if len(columns) > 1 else columns[0]
                        else:
                            x_axis = 'x'
                            y_axis = 'y'
                    except:
                        x_axis = 'x'
                        y_axis = 'y'
                    
                    tool_result = mcp_client.call_tool("generate_chart", {
                        "data_source": detected_file,
                        "chart_type": chart_type,
                        "title": f"{chart_type.title()} Chart",
                        "x_axis": x_axis,
                        "y_axis": y_axis
                    })
                    tool_used = "generate_chart"
                    tool_parameters = {"data_source": detected_file, "chart_type": chart_type}
                    ai_response = f"Creating a {chart_type} chart from {detected_file}."
                else:
                    ai_response = f"Please specify which file to chart. Available files: {', '.join(available_files)}"
                    
            elif any(word in query_lower for word in ['stats', 'statistics', 'analyze', 'summary']):
                if detected_file:
                    tool_result = mcp_client.call_tool("get_data_stats", {"data_source": detected_file})
                    tool_used = "get_data_stats"
                    tool_parameters = {"data_source": detected_file}
                    ai_response = f"Getting comprehensive statistics for {detected_file}."
                else:
                    ai_response = f"Please specify which file to analyze. Available files: {', '.join(available_files)}"
                    
            elif any(word in query_lower for word in ['column', 'field', 'info']):
                if detected_file:
                    tool_result = mcp_client.call_tool("get_column_info", {"data_source": detected_file})
                    tool_used = "get_column_info"
                    tool_parameters = {"data_source": detected_file}
                    ai_response = f"Getting column information for {detected_file}."
                else:
                    ai_response = f"Please specify which file to examine. Available files: {', '.join(available_files)}"
                    
            elif any(word in query_lower for word in ['list', 'files', 'available']):
                tool_result = mcp_client.call_tool("list_data_files", {})
                tool_used = "list_data_files"
                tool_parameters = {}
                ai_response = "Here are all available CSV files in the data directory."
            
            else:
                # Default: show available files and capabilities
                tool_result = mcp_client.call_tool("list_data_files", {})
                tool_used = "list_data_files"
                tool_parameters = {}
                ai_response = f"I can help you analyze CSV data. Available files: {', '.join(available_files)}. Try asking to 'read', 'chart', or 'analyze' a specific file."
        
        return {
            'success': True,
            'ai_response': ai_response,
            'tool_used': tool_used,
            'tool_parameters': tool_parameters,
            'tool_result': tool_result
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }



@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload a CSV file to the data directory"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files are allowed'}), 400
        
        # Save file to data directory
        filepath = Path(f"data/{file.filename}")
        file.save(str(filepath))
        
        return jsonify({
            'success': True,
            'message': f'File {file.filename} uploaded successfully',
            'filename': file.filename
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tools')
def get_tools():
    """Get available tools and resources from MCP server"""
    try:
        # Get tools, resources, and data files using MCP client
        result = get_tools_sync()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def get_tools_sync():
    """Get tools and resources using MCP client (synchronous version)"""
    global mcp_client
    
    try:
        # Connect to MCP server if not already connected
        if not mcp_client.connected:
            mcp_client.connect_to_server()
        
        # Get available data files using MCP tool
        data_files = []
        try:
            file_list_result = mcp_client.call_tool("list_data_files", {})
            if file_list_result:
                files_data = json.loads(file_list_result)
                data_files = files_data.get('available_files', [])
        except:
            if os.path.exists("data"):
                data_files = [f for f in os.listdir("data") if f.endswith('.csv')]
        
        # Get tools and resources
        tools_list = mcp_client.list_tools()
        resources_list = mcp_client.list_resources()
        
        tools = {tool['name']: tool['description'] for tool in tools_list}
        resources = {resource['uri']: resource['description'] for resource in resources_list}
        
        return {
            'success': True,
            'tools': tools,
            'resources': resources,
            'data_files': data_files
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download generated charts or data files"""
    try:
        if filename.startswith('chart_'):
            # Download from output directory
            filepath = Path(f"output/{filename}")
        else:
            # Download from data directory
            filepath = Path(f"data/{filename}")
        
        if not filepath.exists():
            return "File not found", 404
        
        return send_file(str(filepath), as_attachment=True)
        
    except Exception as e:
        return f"Error downloading file: {str(e)}", 500



def main():
    """Main function to run the Flask app"""
    print("Starting MCP Data Analysis Web Application...")
    print("Access the dashboard at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()
