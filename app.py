"""
Flask web application for MCP Data Analysis System
Provides a web interface for data analysis tools
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from pathlib import Path
import sys

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
    """Main dashboard page"""
    try:
        from client.direct_client import DirectClient
        client = DirectClient()
        
        # Get available data files
        data_files = client.list_data_files()
        
        # Get available tools
        tools = client.list_tools()
        
        return render_template('index.html', 
                             data_files=data_files, 
                             tools=tools)
    except Exception as e:
        return f"Error loading dashboard: {str(e)}", 500

@app.route('/api/execute', methods=['POST'])
def execute_tool():
    """Execute a data analysis tool"""
    try:
        from client.direct_client import DirectClient
        client = DirectClient()
        
        data = request.get_json()
        tool_name = data.get('tool')
        parameters = data.get('parameters', {})
        
        if not tool_name:
            return jsonify({'error': 'Tool name is required'}), 400
        
        result = client.execute_tool(tool_name, parameters)
        
        return jsonify({
            'success': True,
            'result': result,
            'tool': tool_name,
            'parameters': parameters
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files')
def list_files():
    """List available data files"""
    try:
        from client.direct_client import DirectClient
        client = DirectClient()
        
        data_files = client.list_data_files()
        
        # Get file info
        file_info = []
        for filename in data_files:
            filepath = Path(f"data/{filename}")
            if filepath.exists():
                stat = filepath.stat()
                file_info.append({
                    'name': filename,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
        
        return jsonify({
            'success': True,
            'files': file_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tools')
def list_tools():
    """List available tools with detailed information"""
    try:
        from client.direct_client import DirectClient
        client = DirectClient()
        
        tools = client.list_tools()
        tool_details = {}
        
        for tool_name in tools.keys():
            info = client.get_tool_info(tool_name)
            if info:
                tool_details[tool_name] = info
        
        return jsonify({
            'success': True,
            'tools': tool_details
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

# Create basic HTML templates if they don't exist
def create_templates():
    """Create basic HTML templates"""
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    # Create index.html
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Data Analysis Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-12">
                <h1 class="mt-4 mb-4">
                    <i class="fas fa-chart-bar"></i> MCP Data Analysis Dashboard
                </h1>
                
                <!-- File Upload Section -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5><i class="fas fa-upload"></i> Upload Data File</h5>
                    </div>
                    <div class="card-body">
                        <input type="file" id="fileInput" accept=".csv" class="form-control mb-2">
                        <button onclick="uploadFile()" class="btn btn-primary">
                            <i class="fas fa-upload"></i> Upload CSV
                        </button>
                    </div>
                </div>
                
                <!-- Available Files -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5><i class="fas fa-database"></i> Available Data Files</h5>
                    </div>
                    <div class="card-body">
                        {% if data_files %}
                            <div class="list-group">
                                {% for file in data_files %}
                                <div class="list-group-item">
                                    <i class="fas fa-file-csv"></i> {{ file }}
                                    <button onclick="analyzeFile('{{ file }}')" class="btn btn-sm btn-outline-primary float-end">
                                        <i class="fas fa-chart-line"></i> Analyze
                                    </button>
                                </div>
                                {% endfor %}
                            </div>
                        {% else %}
                            <p class="text-muted">No CSV files found. Upload a file to get started.</p>
                        {% endif %}
                    </div>
                </div>
                
                <!-- Tool Execution -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5><i class="fas fa-tools"></i> Data Analysis Tools</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <label class="form-label">Tool:</label>
                                <select id="toolSelect" class="form-select">
                                    <option value="">Select a tool...</option>
                                    {% for tool, desc in tools.items() %}
                                    <option value="{{ tool }}">{{ tool }} - {{ desc }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Data File:</label>
                                <select id="dataFileSelect" class="form-select">
                                    <option value="">Select a file...</option>
                                    {% for file in data_files %}
                                    <option value="{{ file }}">{{ file }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                        
                        <div class="mt-3">
                            <label class="form-label">Additional Parameters (JSON):</label>
                            <textarea id="paramsInput" class="form-control" rows="3" placeholder='{"chart_type": "bar", "title": "My Chart"}'></textarea>
                        </div>
                        
                        <div class="mt-3">
                            <button onclick="executeTool()" class="btn btn-success">
                                <i class="fas fa-play"></i> Execute Tool
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Results -->
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-bar"></i> Results</h5>
                    </div>
                    <div class="card-body">
                        <div id="results" class="text-muted">
                            No results yet. Execute a tool to see output.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select a file');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('File uploaded successfully!');
                    location.reload();
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                alert('Error uploading file: ' + error);
            });
        }
        
        function analyzeFile(filename) {
            const params = {
                tool: 'get_data_stats',
                parameters: {
                    data_source: filename
                }
            };
            
            executeToolInternal(params);
        }
        
        function executeTool() {
            const tool = document.getElementById('toolSelect').value;
            const dataFile = document.getElementById('dataFileSelect').value;
            const paramsText = document.getElementById('paramsInput').value;
            
            if (!tool) {
                alert('Please select a tool');
                return;
            }
            
            let parameters = {};
            if (dataFile) {
                parameters.data_source = dataFile;
            }
            
            if (paramsText) {
                try {
                    const additionalParams = JSON.parse(paramsText);
                    parameters = {...parameters, ...additionalParams};
                } catch (e) {
                    alert('Invalid JSON in parameters');
                    return;
                }
            }
            
            const params = {
                tool: tool,
                parameters: parameters
            };
            
            executeToolInternal(params);
        }
        
        function executeToolInternal(params) {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Executing...';
            
            fetch('/api/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    resultsDiv.innerHTML = `
                        <div class="alert alert-success">
                            <strong>Tool:</strong> ${data.tool}<br>
                            <strong>Parameters:</strong> ${JSON.stringify(data.parameters, null, 2)}
                        </div>
                        <pre>${data.result}</pre>
                    `;
                } else {
                    resultsDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <strong>Error:</strong> ${data.error}
                        </div>
                    `;
                }
            })
            .catch(error => {
                resultsDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Network Error:</strong> ${error}
                    </div>
                `;
            });
        }
    </script>
</body>
</html>"""
    
    with open(templates_dir / "index.html", "w") as f:
        f.write(index_html)

def main():
    """Main function to run the Flask app"""
    # Create templates if they don't exist
    create_templates()
    
    print("Starting MCP Data Analysis Web Application...")
    print("Access the dashboard at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()
