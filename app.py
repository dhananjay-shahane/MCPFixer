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
        
        # Get available tools from MCP server
        tools = {
            "read_csv": "Read CSV file content from data directory",
            "get_data_stats": "Get comprehensive statistics about CSV data",
            "get_column_info": "Get detailed information about columns in dataset",
            "filter_data": "Filter CSV data by column value with various operations",
            "generate_chart": "Generate charts from CSV data (bar, line, scatter, pie)",
            "list_data_files": "List all available CSV files in the data directory",
            "execute_script": "Execute analysis scripts"
        }
        
        resources = {"csv://{filename}": "Access CSV file content as a resource"}
        
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
        from server.server import read_csv, get_data_stats, generate_chart, list_data_files, get_column_info, filter_data
        
        data = request.get_json()
        user_query = data.get('message', '')
        
        if not user_query:
            return jsonify({'error': 'Message is required'}), 400
        
        tool_result = None
        tool_used = None
        tool_parameters = None
        ai_response = ""
        
        # Parse user query for tool requests
        query_lower = user_query.lower()
        
        if "read" in query_lower and "csv" in query_lower:
            # Extract filename from query
            words = user_query.split()
            csv_file = None
            for word in words:
                if word.endswith('.csv'):
                    csv_file = word
                    break
            
            if not csv_file:
                # Check for common file patterns
                for filename in ["employee_data.csv", "sales_data.csv", "sample_data.csv", "inventory_data.csv"]:
                    if filename.replace("_", " ").replace(".csv", "") in query_lower:
                        csv_file = filename
                        break
            
            if csv_file:
                tool_parameters = {"filename": csv_file}
                tool_result = read_csv(csv_file)
                tool_used = "read_csv"
                ai_response = f"Reading {csv_file} from the data directory."
            else:
                ai_response = "Please specify a CSV filename. Available files can be found in the data directory."
        
        elif "chart" in query_lower or "visualiz" in query_lower or "graph" in query_lower:
            # Handle chart generation
            chart_type = "bar"
            if "pie" in query_lower:
                chart_type = "pie"
            elif "line" in query_lower:
                chart_type = "line"
            elif "scatter" in query_lower:
                chart_type = "scatter"
            
            # Extract CSV file
            csv_file = "sample_data.csv"
            words = user_query.split()
            for word in words:
                if word.endswith('.csv'):
                    csv_file = word
                    break
            
            try:
                import pandas as pd
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
                tool_result = generate_chart(csv_file, chart_type, tool_parameters["title"], x_axis, y_axis)
                tool_used = "generate_chart"
                ai_response = f"Creating a {chart_type} chart from {csv_file}."
            except Exception as e:
                ai_response = f"Error creating chart: {str(e)}"
        
        elif "stats" in query_lower or "statistics" in query_lower or "analyze" in query_lower:
            # Handle statistics requests
            csv_file = "sample_data.csv"
            words = user_query.split()
            for word in words:
                if word.endswith('.csv'):
                    csv_file = word
                    break
            
            tool_parameters = {"data_source": csv_file}
            tool_result = get_data_stats(csv_file)
            tool_used = "get_data_stats"
            ai_response = f"Getting statistics for {csv_file}."
        
        elif "list" in query_lower and "file" in query_lower:
            tool_result = list_data_files()
            tool_used = "list_data_files"
            ai_response = "Listing all available CSV files in the data directory."
        
        else:
            ai_response = "I can help you analyze CSV data. Try:\n• 'read filename.csv' - to view file contents\n• 'create a chart from filename.csv' - to generate visualizations\n• 'get stats for filename.csv' - for data analysis\n• 'list files' - to see available data files"
        
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
        # Get available data files
        data_files = []
        if os.path.exists("data"):
            data_files = [f for f in os.listdir("data") if f.endswith('.csv')]
        
        tools = {
            "read_csv": "Read CSV file content from data directory",
            "get_data_stats": "Get comprehensive statistics about CSV data",
            "get_column_info": "Get detailed information about columns in dataset",
            "filter_data": "Filter CSV data by column value with various operations",
            "generate_chart": "Generate charts from CSV data (bar, line, scatter, pie)",
            "list_data_files": "List all available CSV files in the data directory"
        }
        
        resources = {"csv://{filename}": "Access CSV file content as a resource"}
        
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
