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
        from client.direct_client import DirectClient
        client = DirectClient()
        
        # Get available data files for context
        data_files = client.list_data_files()
        
        # Get available tools and resources for the UI
        tools = client.list_tools()
        resources = client.list_resources() if hasattr(client, 'list_resources') else {}
        
        print(f"DEBUG: data_files = {data_files}")
        print(f"DEBUG: tools = {tools}")
        print(f"DEBUG: resources = {resources}")
        
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
    """Process natural language chat queries"""
    try:
        from client.ollama_client import OllamaClient
        from client.direct_client import DirectClient
        
        data = request.get_json()
        user_query = data.get('message', '')
        
        if not user_query:
            return jsonify({'error': 'Message is required'}), 400
        
        # Initialize clients
        direct_client = DirectClient()
        
        # Parse user query for direct tool requests or natural language
        tool_result = None
        tool_used = None
        tool_parameters = None
        ai_response = ""
        
        # Check if it's a direct tool request pattern
        if user_query.startswith('#'):
            # Handle # syntax: #tool_name params
            parts = user_query[1:].split(' ', 1)
            tool_name = parts[0]
            tool_params_str = parts[1] if len(parts) > 1 else ""
            
            # Parse parameters
            try:
                import json
                tool_parameters = json.loads(tool_params_str) if tool_params_str.startswith('{') else {"filename": tool_params_str}
            except:
                tool_parameters = {"filename": tool_params_str} if tool_params_str else {}
            
            tool_result = direct_client.execute_tool(tool_name, tool_parameters)
            tool_used = tool_name
            ai_response = f"Executed {tool_name} with parameters: {tool_parameters}"
            
        else:
            # Parse natural language queries for common patterns
            query_lower = user_query.lower()
            
            if "read" in query_lower and ("csv" in query_lower or any(f in query_lower for f in ["employee", "sales", "sample", "inventory"])):
                # Extract filename
                for filename in ["employee_data.csv", "sales_data.csv", "sample_data.csv", "inventory_data.csv"]:
                    if filename.replace("_", " ").replace(".csv", "") in query_lower or filename in query_lower:
                        tool_parameters = {"filename": filename}
                        tool_result = direct_client.execute_tool("read_csv", tool_parameters)
                        tool_used = "read_csv"
                        ai_response = f"Reading the CSV file containing {filename.replace('.csv', '').replace('_', ' ')} from the 'data' directory."
                        break
                else:
                    # Try to extract any CSV filename
                    words = user_query.split()
                    for word in words:
                        if word.endswith('.csv'):
                            tool_parameters = {"filename": word}
                            tool_result = direct_client.execute_tool("read_csv", tool_parameters)
                            tool_used = "read_csv"
                            ai_response = f"Reading the CSV file {word} from the 'data' directory."
                            break
            
            elif "chart" in query_lower or "visualiz" in query_lower or "graph" in query_lower:
                # Handle chart generation requests
                chart_type = "bar"
                if "pie" in query_lower:
                    chart_type = "pie"
                elif "line" in query_lower:
                    chart_type = "line"
                elif "scatter" in query_lower:
                    chart_type = "scatter"
                
                # Extract CSV file
                csv_file = "sample_data.csv"  # default
                for filename in ["employee_data.csv", "sales_data.csv", "sample_data.csv", "inventory_data.csv"]:
                    if filename.replace("_", " ").replace(".csv", "") in query_lower or filename in query_lower:
                        csv_file = filename
                        break
                
                # Try to determine columns from CSV
                import pandas as pd
                try:
                    df = pd.read_csv(f"data/{csv_file}")
                    columns = list(df.columns)
                    x_axis = columns[0] if len(columns) > 0 else "x"
                    y_axis = columns[1] if len(columns) > 1 else columns[0]
                    
                    tool_parameters = {
                        "data_source": csv_file,
                        "chart_type": chart_type,
                        "title": f"{chart_type.title()} Chart from {csv_file}",
                        "x_axis": x_axis,
                        "y_axis": y_axis
                    }
                    tool_result = direct_client.execute_tool("generate_chart", tool_parameters)
                    tool_used = "generate_chart"
                    ai_response = f"Creating a {chart_type} chart from {csv_file} using columns {x_axis} and {y_axis}."
                except:
                    ai_response = f"Please specify which CSV file to use for the chart. Available files: employee_data.csv, sales_data.csv, sample_data.csv, inventory_data.csv"
            
            elif "stats" in query_lower or "statistics" in query_lower or "analyze" in query_lower:
                # Handle statistics requests
                csv_file = "sample_data.csv"  # default
                for filename in ["employee_data.csv", "sales_data.csv", "sample_data.csv", "inventory_data.csv"]:
                    if filename.replace("_", " ").replace(".csv", "") in query_lower or filename in query_lower:
                        csv_file = filename
                        break
                
                tool_parameters = {"data_source": csv_file}
                tool_result = direct_client.execute_tool("get_data_stats", tool_parameters)
                tool_used = "get_data_stats"
                ai_response = f"Getting comprehensive statistics for {csv_file}."
            
            elif "list" in query_lower and "file" in query_lower:
                # List available files
                tool_result = direct_client.execute_tool("list_data_files", {})
                tool_used = "list_data_files"
                ai_response = "Listing all available CSV files in the data directory."
            
            elif "script" in query_lower and "execute" in query_lower:
                # Handle script execution
                script_name = "bar_chart_generator.py"  # default
                if "pie" in query_lower:
                    script_name = "pie_chart_generator.py"
                elif "analyzer" in query_lower:
                    script_name = "data_analyzer.py"
                
                csv_file = "sample_data.csv"  # default
                for filename in ["employee_data.csv", "sales_data.csv", "sample_data.csv", "inventory_data.csv"]:
                    if filename.replace("_", " ").replace(".csv", "") in query_lower or filename in query_lower:
                        csv_file = filename
                        break
                
                tool_parameters = {"script_name": script_name, "csv_file": csv_file}
                tool_result = direct_client.execute_tool("execute_script", tool_parameters)
                tool_used = "execute_script"
                ai_response = f"Executing {script_name} with {csv_file}."
            
            # Try Ollama as fallback if no direct pattern matched
            if not tool_used:
                try:
                    ollama_url = 'http://127.0.0.1:11434'
                    ollama_client = OllamaClient(model="llama3.2:1b", base_url=ollama_url)
                    response = ollama_client.process_query(user_query)
                    
                    if response and response.get("tool"):
                        tool_result = direct_client.execute_tool(response["tool"], response["parameters"])
                        tool_used = response["tool"]
                        tool_parameters = response["parameters"]
                        ai_response = response['explanation']
                    else:
                        ai_response = response['explanation'] if response else "I understand you want to work with data, but I need more specific instructions. Try: 'read sample_data.csv' or 'create a chart from sales_data.csv'"
                except:
                    ai_response = "I understand you want to work with data. Here are some things you can try:\n• 'read sample_data.csv' - to read a CSV file\n• 'create a bar chart from sales_data.csv' - to generate charts\n• 'get stats for employee_data.csv' - for data analysis\n• Click the gear button to see all available tools"
        
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
    """Get available tools and resources"""
    try:
        from client.direct_client import DirectClient
        client = DirectClient()
        
        tools = client.list_tools()
        resources = client.list_resources() if hasattr(client, 'list_resources') else {}
        data_files = client.list_data_files()
        
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
