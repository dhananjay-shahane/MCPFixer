"""
Flask web application for MCP Data Analysis System
Provides a web interface for data analysis tools
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from pathlib import Path
import sys
import re

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Initialize Flask app
app = Flask(__name__)


# Ensure required directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

@app.route('/')
def index():
    """AI Chat Interface"""
    try:
        from server.server import mcp
        
        # Get available data files
        data_files = []
        if os.path.exists("data"):
            data_files = [f for f in os.listdir("data") if f.endswith('.csv')]
        
        # Get available tools directly from MCP server registry
        tools = {}
        resources = {}
        
        # Extract tools and resources from MCP server using correct API
        if hasattr(mcp, '_tool_manager') and hasattr(mcp._tool_manager, '_tools'):
            for tool_name, tool in mcp._tool_manager._tools.items():
                tools[tool_name] = getattr(tool, 'description', f"MCP tool: {tool_name}") or f"MCP tool: {tool_name}"
        
        # Try to get resources if available (FastMCP may store these differently)
        if hasattr(mcp, '_resource_manager') and hasattr(mcp._resource_manager, '_resources'):
            for resource_pattern, resource in mcp._resource_manager._resources.items():
                resources[resource_pattern] = getattr(resource, 'description', f"MCP resource: {resource_pattern}") or f"MCP resource: {resource_pattern}"
        else:
            # Fallback for resources - may be stored differently in FastMCP
            resources = {"csv://{filename}": "Read CSV file content as a resource"}
        
        import time
        timestamp = int(time.time())
        return render_template('chat.html', 
                             data_files=data_files, 
                             tools=tools, 
                             resources=resources, 
                             timestamp=timestamp)
    except Exception as e:
        print(f"ERROR loading chat interface: {str(e)}")
        return f"Error loading chat interface: {str(e)}", 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process natural language chat queries using MCP server"""
    try:
        from server.server import mcp
        
        data = request.get_json()
        user_query = data.get('message', '')
        tool_name = data.get('tool_name', None)
        tool_params = data.get('tool_params', {})
        
        if not user_query and not tool_name:
            return jsonify({'error': 'Message or tool name is required'}), 400
        
        tool_result = None
        tool_used = None
        tool_parameters = None
        ai_response = ""
        
        # Direct tool execution if tool_name is provided
        if tool_name:
            try:
                if hasattr(mcp, '_tool_manager') and tool_name in mcp._tool_manager._tools:
                    tool = mcp._tool_manager._tools[tool_name]
                    tool_func = tool.func
                    
                    # Execute tool with parameters
                    if tool_name == "read_csv":
                        filename = tool_params.get('filename', '')
                        if filename:
                            tool_result = tool_func(filename)
                            tool_used = tool_name
                            tool_parameters = {"filename": filename}
                            ai_response = f"Reading {filename} from the data directory."
                        else:
                            ai_response = "Please provide a filename parameter."
                            
                    elif tool_name == "get_data_stats":
                        data_source = tool_params.get('data_source', '')
                        if data_source:
                            tool_result = tool_func(data_source)
                            tool_used = tool_name
                            tool_parameters = {"data_source": data_source}
                            ai_response = f"Getting statistics for {data_source}."
                        else:
                            ai_response = "Please provide a data_source parameter."
                            
                    elif tool_name == "generate_chart":
                        data_source = tool_params.get('data_source', '')
                        chart_type = tool_params.get('chart_type', 'bar')
                        title = tool_params.get('title', 'Chart')
                        x_axis = tool_params.get('x_axis', 'x')
                        y_axis = tool_params.get('y_axis', 'y')
                        
                        if data_source:
                            tool_result = tool_func(data_source, chart_type, title, x_axis, y_axis)
                            tool_used = tool_name
                            tool_parameters = tool_params
                            ai_response = f"Creating a {chart_type} chart from {data_source}."
                        else:
                            ai_response = "Please provide a data_source parameter."
                            
                    elif tool_name == "get_column_info":
                        data_source = tool_params.get('data_source', '')
                        column = tool_params.get('column', None)
                        if data_source:
                            tool_result = tool_func(data_source, column)
                            tool_used = tool_name
                            tool_parameters = tool_params
                            ai_response = f"Getting column information for {data_source}."
                        else:
                            ai_response = "Please provide a data_source parameter."
                            
                    elif tool_name == "filter_data":
                        data_source = tool_params.get('data_source', '')
                        column = tool_params.get('column', '')
                        value = tool_params.get('value', '')
                        operation = tool_params.get('operation', 'equals')
                        
                        if data_source and column and value:
                            tool_result = tool_func(data_source, column, value, operation)
                            tool_used = tool_name
                            tool_parameters = tool_params
                            ai_response = f"Filtering {data_source} where {column} {operation} {value}."
                        else:
                            ai_response = "Please provide data_source, column, and value parameters."
                            
                    elif tool_name == "list_data_files":
                        tool_result = tool_func()
                        tool_used = tool_name
                        tool_parameters = {}
                        ai_response = "Listing all available CSV files in the data directory."
                        
                    elif tool_name == "execute_script":
                        script_name = tool_params.get('script_name', '')
                        csv_file = tool_params.get('csv_file', '')
                        args = tool_params.get('args', '')
                        
                        if script_name and csv_file:
                            tool_result = tool_func(script_name, csv_file, args)
                            tool_used = tool_name
                            tool_parameters = tool_params
                            ai_response = f"Executing {script_name} with {csv_file}."
                        else:
                            ai_response = "Please provide script_name and csv_file parameters."
                    
                    else:
                        # Generic tool execution for other tools
                        try:
                            tool_result = tool_func(**tool_params)
                            tool_used = tool_name
                            tool_parameters = tool_params
                            ai_response = f"Executed {tool_name} with parameters: {tool_params}"
                        except Exception as e:
                            ai_response = f"Error executing {tool_name}: {str(e)}"
                            
                else:
                    ai_response = f"Unknown tool: {tool_name}"
                    
            except Exception as e:
                ai_response = f"Error executing {tool_name}: {str(e)}"
        
        else:
            # Natural language processing with intelligent tool selection
            query_lower = user_query.lower()
            
            # Get available files using MCP tool
            available_files = []
            try:
                if hasattr(mcp, '_tool_manager') and 'list_data_files' in mcp._tool_manager._tools:
                    tool_func = mcp._tool_manager._tools['list_data_files'].func
                    file_list_result = tool_func()
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
            
            # Tool selection based on query intent - using MCP server tools
            if any(word in query_lower for word in ['read', 'show', 'display', 'view', 'content']):
                if detected_file and hasattr(mcp, '_tool_manager') and 'read_csv' in mcp._tool_manager._tools:
                    tool_func = mcp._tool_manager._tools['read_csv'].func
                    tool_result = tool_func(detected_file)
                    tool_used = "read_csv"
                    tool_parameters = {"filename": detected_file}
                    ai_response = f"Reading {detected_file} from the data directory."
                else:
                    ai_response = f"Please specify which file to read. Available files: {', '.join(available_files)}"
                    
            elif any(word in query_lower for word in ['chart', 'graph', 'plot', 'visualiz']):
                if detected_file and hasattr(mcp, '_tool_manager') and 'generate_chart' in mcp._tool_manager._tools:
                    chart_type = 'bar'
                    if 'pie' in query_lower: chart_type = 'pie'
                    elif 'line' in query_lower: chart_type = 'line'
                    elif 'scatter' in query_lower: chart_type = 'scatter'
                    
                    # Try to get column info for smart defaults using MCP tools
                    try:
                        # Use read_csv tool to get column information
                        if hasattr(mcp, '_tool_manager') and 'read_csv' in mcp._tool_manager._tools:
                            read_func = mcp._tool_manager._tools['read_csv'].func
                            csv_data = read_func(detected_file)
                            # Parse first line to get columns
                            lines = csv_data.split('\n')
                            if lines:
                                columns = lines[0].split()
                                x_axis = columns[0] if columns else 'x'
                                y_axis = columns[1] if len(columns) > 1 else columns[0]
                            else:
                                x_axis = 'x'
                                y_axis = 'y'
                        else:
                            x_axis = 'x'
                            y_axis = 'y'
                        
                        chart_func = mcp._tool_manager._tools['generate_chart'].func
                        tool_result = chart_func(detected_file, chart_type, f"{chart_type.title()} Chart", x_axis, y_axis)
                        tool_used = "generate_chart"
                        tool_parameters = {"data_source": detected_file, "chart_type": chart_type, "x_axis": x_axis, "y_axis": y_axis}
                        ai_response = f"Creating a {chart_type} chart from {detected_file}."
                    except Exception as e:
                        ai_response = f"Error creating chart: {str(e)}"
                else:
                    ai_response = f"Please specify which file to chart. Available files: {', '.join(available_files)}"
                    
            elif any(word in query_lower for word in ['stats', 'statistics', 'analyze', 'summary']):
                if detected_file and hasattr(mcp, '_tool_manager') and 'get_data_stats' in mcp._tool_manager._tools:
                    tool_func = mcp._tool_manager._tools['get_data_stats'].func
                    tool_result = tool_func(detected_file)
                    tool_used = "get_data_stats"
                    tool_parameters = {"data_source": detected_file}
                    ai_response = f"Getting comprehensive statistics for {detected_file}."
                else:
                    ai_response = f"Please specify which file to analyze. Available files: {', '.join(available_files)}"
                    
            elif any(word in query_lower for word in ['column', 'field', 'info']):
                if detected_file and hasattr(mcp, '_tool_manager') and 'get_column_info' in mcp._tool_manager._tools:
                    tool_func = mcp._tool_manager._tools['get_column_info'].func
                    tool_result = tool_func(detected_file)
                    tool_used = "get_column_info"
                    tool_parameters = {"data_source": detected_file}
                    ai_response = f"Getting column information for {detected_file}."
                else:
                    ai_response = f"Please specify which file to examine. Available files: {', '.join(available_files)}"
                    
            elif any(word in query_lower for word in ['list', 'files', 'available']):
                if hasattr(mcp, '_tool_manager') and 'list_data_files' in mcp._tool_manager._tools:
                    tool_func = mcp._tool_manager._tools['list_data_files'].func
                    tool_result = tool_func()
                    tool_used = "list_data_files"
                    tool_parameters = {}
                    ai_response = "Here are all available CSV files in the data directory."
                else:
                    ai_response = "File listing tool not available."
                
            else:
                # Default: show available files and capabilities
                if hasattr(mcp, '_tool_manager') and 'list_data_files' in mcp._tool_manager._tools:
                    tool_func = mcp._tool_manager._tools['list_data_files'].func
                    tool_result = tool_func()
                    tool_used = "list_data_files"
                    tool_parameters = {}
                    ai_response = f"I can help you analyze CSV data. Available files: {', '.join(available_files)}. Try asking to 'read', 'chart', or 'analyze' a specific file."
                else:
                    tool_names = list(mcp._tool_manager._tools.keys()) if hasattr(mcp, '_tool_manager') and hasattr(mcp._tool_manager, '_tools') else []
                    ai_response = f"I can help you analyze CSV data. Available tools: {', '.join(tool_names)}. Try asking about a specific file or tool."
        
        return jsonify({
            'success': True,
            'ai_response': ai_response,
            'tool_used': tool_used,
            'tool_parameters': tool_parameters,
            'tool_result': tool_result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



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
        from server.server import mcp
        
        # Get available data files using MCP tool if available
        data_files = []
        try:
            if hasattr(mcp, '_tool_manager') and 'list_data_files' in mcp._tool_manager._tools:
                tool_func = mcp._tool_manager._tools['list_data_files'].func
                file_list_result = tool_func()
                if file_list_result:
                    files_data = json.loads(file_list_result)
                    data_files = files_data.get('available_files', [])
        except:
            if os.path.exists("data"):
                data_files = [f for f in os.listdir("data") if f.endswith('.csv')]
        
        # Get tools directly from MCP server registry using correct API
        tools = {}
        if hasattr(mcp, '_tool_manager') and hasattr(mcp._tool_manager, '_tools'):
            for tool_name, tool in mcp._tool_manager._tools.items():
                tools[tool_name] = getattr(tool, 'description', f"MCP tool: {tool_name}") or f"MCP tool: {tool_name}"
        
        # Get resources from MCP server registry
        resources = {}
        if hasattr(mcp, '_resource_manager') and hasattr(mcp._resource_manager, '_resources'):
            for resource_pattern, resource in mcp._resource_manager._resources.items():
                resources[resource_pattern] = getattr(resource, 'description', f"MCP resource: {resource_pattern}") or f"MCP resource: {resource_pattern}"
        else:
            # Fallback for resources
            resources = {"csv://{filename}": "Read CSV file content as a resource"}
        
        return jsonify({
            'success': True,
            'tools': tools,
            'resources': resources,
            'data_files': data_files
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
