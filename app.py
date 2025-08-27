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

def simple_query_parser(query, direct_client):
    """Enhanced keyword-based query parser when Ollama is not available"""
    query_lower = query.lower()
    
    # Get available data files
    data_files = direct_client.list_data_files()
    default_file = data_files[0] if data_files else None
    
    # Try to extract specific filename from query
    detected_file = None
    for file in data_files:
        if file.lower() in query_lower or file.split('.')[0].lower() in query_lower:
            detected_file = file
            break
    
    # Use detected file or default
    target_file = detected_file or default_file
    
    # Enhanced pattern matching for different types of queries
    
    # Statistics and analysis queries
    if any(word in query_lower for word in ['stats', 'statistics', 'summary', 'analyze', 'analysis', 'info', 'describe', 'overview']):
        if target_file:
            return {
                "tool": "get_data_stats",
                "parameters": {"data_source": target_file},
                "explanation": f"📊 Analyzing {target_file} and generating comprehensive statistics including data types, missing values, and summary statistics."
            }
        else:
            return {
                "tool": None,
                "parameters": {},
                "explanation": "📁 I'd love to analyze your data! Please upload a CSV file first, then ask me to analyze it."
            }
    
    # Chart and visualization queries
    elif any(word in query_lower for word in ['chart', 'graph', 'plot', 'visualize', 'visualization', 'draw']):
        if target_file:
            # Smart chart type detection
            chart_type = "bar"
            if any(word in query_lower for word in ['line', 'trend', 'time', 'over time']):
                chart_type = "line"
            elif any(word in query_lower for word in ['scatter', 'correlation', 'relationship']):
                chart_type = "scatter"
            elif any(word in query_lower for word in ['pie', 'distribution', 'proportion']):
                chart_type = "pie"
            
            # Try to detect column names from query
            # Get column info first to make better assumptions
            try:
                column_result = direct_client.execute_tool("get_column_info", {"data_source": target_file})
                # This is a simplified approach - in reality you'd parse the JSON response
                x_axis = "index"  # Safe default
                y_axis = "value"  # Safe default
            except:
                x_axis = "index"
                y_axis = "value"
            
            return {
                "tool": "generate_chart",
                "parameters": {
                    "data_source": target_file,
                    "chart_type": chart_type,
                    "title": f"{target_file.split('.')[0]} - {chart_type.title()} Chart",
                    "x_axis": x_axis,
                    "y_axis": y_axis
                },
                "explanation": f"📈 Creating a {chart_type} chart from {target_file}. I'll use the most suitable columns for visualization."
            }
        else:
            return {
                "tool": None,
                "parameters": {},
                "explanation": "📊 I'd love to create a chart for you! Please upload a CSV file first."
            }
    
    # Data reading and display queries
    elif any(word in query_lower for word in ['read', 'show', 'display', 'content', 'view', 'see', 'preview']):
        if target_file:
            return {
                "tool": "read_csv",
                "parameters": {"filename": target_file},
                "explanation": f"📋 Reading and displaying the contents of {target_file}."
            }
        else:
            return {
                "tool": None,
                "parameters": {},
                "explanation": "📄 I'd love to show your data! Please upload a CSV file first."
            }
    
    # Column information queries
    elif any(word in query_lower for word in ['column', 'columns', 'field', 'fields', 'structure', 'schema']):
        if target_file:
            return {
                "tool": "get_column_info",
                "parameters": {"data_source": target_file},
                "explanation": f"🏗️ Getting detailed information about the structure and columns in {target_file}."
            }
        else:
            return {
                "tool": None,
                "parameters": {},
                "explanation": "🗂️ I'd love to show column information! Please upload a CSV file first."
            }
    
    # Filter queries (enhanced parsing)
    elif any(word in query_lower for word in ['filter', 'search', 'find', 'where', 'select']):
        if target_file:
            # Try to extract filter conditions
            # Look for patterns like "where X > Y" or "X equals Y"
            filter_patterns = [
                (r'where\s+(\w+)\s*([><=!]+)\s*(\w+)', 'where clause'),
                (r'(\w+)\s*(equals?|is|=)\s*(\w+)', 'equals condition'),
                (r'(\w+)\s*>\s*(\w+)', 'greater than'),
                (r'(\w+)\s*<\s*(\w+)', 'less than')
            ]
            
            for pattern, description in filter_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    column = match.group(1)
                    if len(match.groups()) >= 3:
                        value = match.group(3)
                        operator = match.group(2) if len(match.groups()) >= 3 else 'equals'
                        
                        operation = 'equals'
                        if '>' in operator:
                            operation = 'greater'
                        elif '<' in operator:
                            operation = 'less'
                        elif '!' in operator or 'not' in operator:
                            operation = 'not_equals'
                        
                        return {
                            "tool": "filter_data",
                            "parameters": {
                                "data_source": target_file,
                                "column": column,
                                "value": value,
                                "operation": operation
                            },
                            "explanation": f"🔍 Filtering {target_file} where {column} {operation} {value}."
                        }
            
            # If no specific pattern found, ask for clarification
            return {
                "tool": None,
                "parameters": {},
                "explanation": f"🔍 I can filter {target_file} for you! Please specify the condition more clearly, like: 'show rows where age > 25' or 'filter by department equals Engineering'."
            }
        else:
            return {
                "tool": None,
                "parameters": {},
                "explanation": "🔍 I'd love to filter data for you! Please upload a CSV file first."
            }
    
    # Help and greeting queries
    elif any(word in query_lower for word in ['help', 'hello', 'hi', 'what', 'how', 'can you']):
        if data_files:
            return {
                "tool": None,
                "parameters": {},
                "explanation": f"👋 Hi! I'm your AI data analysis assistant. I can help you with:\n\n📊 **Analysis**: 'analyze {data_files[0]}'\n📈 **Charts**: 'create a bar chart'\n📋 **View data**: 'show me the data'\n🏗️ **Structure**: 'show columns'\n🔍 **Filter**: 'filter where age > 25'\n\nAvailable files: {', '.join(data_files)}\n\nWhat would you like to explore?"
            }
        else:
            return {
                "tool": None,
                "parameters": {},
                "explanation": "👋 Hello! I'm your AI data analysis assistant. I can help you analyze CSV files, create charts, and explore your data.\n\n🚀 **Get started**: Upload a CSV file, then ask me questions like:\n• 'analyze my data'\n• 'create a chart'\n• 'show me the columns'\n\nWhat data would you like to explore today?"
            }
    
    # Default response for unclear queries
    else:
        if data_files:
            return {
                "tool": None,
                "parameters": {},
                "explanation": f"🤔 I'm not sure exactly what you want to do, but I can help you with your data! Available files: {', '.join(data_files)}\n\nTry asking:\n• 'analyze data' - for statistics\n• 'create chart' - for visualizations\n• 'show data' - to view contents\n• 'show columns' - for structure info"
            }
        else:
            return {
                "tool": None,
                "parameters": {},
                "explanation": "🤖 I'm your data analysis assistant! Upload a CSV file to get started, then I can help you analyze it, create charts, and explore your data.\n\nOnce you upload a file, try asking:\n• 'analyze my data'\n• 'create a bar chart'\n• 'show me the data'"
            }

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
        
        return render_template('chat.html', data_files=data_files)
    except Exception as e:
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
        
        # Try to connect to Ollama, but fall back to simple parsing if it fails
        try:
            # Check if we have an external Ollama URL in environment
            import os
            ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
            ollama_client = OllamaClient(model="llama3.2", base_url=ollama_url)
            
            # Test connection first
            import requests
            test_response = requests.get(f"{ollama_url}/api/tags", timeout=3)
            if test_response.status_code != 200:
                raise ConnectionError("Ollama not accessible")
            
            # Process query with Ollama
            response = ollama_client.process_query(user_query)
            
            if response and response.get("tool"):
                # Execute the suggested tool
                tool_result = direct_client.execute_tool(
                    response["tool"], 
                    response["parameters"]
                )
                
                return jsonify({
                    'success': True,
                    'ai_response': response['explanation'],
                    'tool_used': response['tool'],
                    'tool_parameters': response['parameters'],
                    'tool_result': tool_result
                })
            else:
                # Just return AI explanation
                return jsonify({
                    'success': True,
                    'ai_response': response['explanation'] if response else "I couldn't process your request.",
                    'tool_used': None,
                    'tool_result': None
                })
                
        except (ConnectionError, requests.exceptions.RequestException, requests.exceptions.Timeout):
            # Fallback: Simple keyword-based tool selection
            response = simple_query_parser(user_query, direct_client)
            
            if response.get("tool"):
                tool_result = direct_client.execute_tool(
                    response["tool"], 
                    response["parameters"]
                )
                
                return jsonify({
                    'success': True,
                    'ai_response': response['explanation'],
                    'tool_used': response['tool'],
                    'tool_parameters': response['parameters'],
                    'tool_result': tool_result
                })
            else:
                return jsonify({
                    'success': True,
                    'ai_response': response['explanation'],
                    'tool_used': None,
                    'tool_result': None
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
    """Create chat interface template"""
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    # Create chat.html
    chat_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Data Analysis Assistant</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .chat-container {
            max-width: 800px;
            margin: 20px auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
            height: calc(100vh - 40px);
            display: flex;
            flex-direction: column;
        }
        .chat-header {
            background: linear-gradient(90deg, #4CAF50, #45a049);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .message {
            max-width: 80%;
            padding: 15px 20px;
            border-radius: 20px;
            word-wrap: break-word;
        }
        .user-message {
            background: #e3f2fd;
            align-self: flex-end;
            border-bottom-right-radius: 5px;
        }
        .ai-message {
            background: #f5f5f5;
            align-self: flex-start;
            border-bottom-left-radius: 5px;
        }
        .tool-result {
            background: #e8f5e8;
            border-left: 4px solid #4CAF50;
            margin-top: 10px;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            white-space: pre-wrap;
            font-size: 0.9em;
        }
        .chat-input-container {
            padding: 20px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
        }
        .chat-input {
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            padding: 15px 20px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        .chat-input:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 0 0.2rem rgba(76, 175, 80, 0.25);
        }
        .send-button {
            background: linear-gradient(90deg, #4CAF50, #45a049);
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            color: white;
            font-size: 18px;
            transition: transform 0.2s;
        }
        .send-button:hover {
            transform: scale(1.1);
        }
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            color: #666;
            font-style: italic;
        }
        .typing-dots {
            display: flex;
            gap: 3px;
        }
        .typing-dot {
            width: 8px;
            height: 8px;
            background: #666;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        .data-files-info {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 10px;
            font-size: 0.9em;
        }
        .scroll-to-bottom {
            position: sticky;
            bottom: 10px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h2><i class="fas fa-robot"></i> AI Data Analysis Assistant</h2>
            <p class="mb-0">Ask me anything about your data!</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            {% if data_files %}
            <div class="data-files-info">
                <i class="fas fa-info-circle"></i> <strong>Available data files:</strong> {{ ', '.join(data_files) }}
            </div>
            {% endif %}
            
            <div class="message ai-message">
                <i class="fas fa-robot"></i> <strong>AI:</strong> Hello! I'm your data analysis assistant. I can help you:
                <ul class="mt-2 mb-0">
                    <li>Read and analyze CSV files</li>
                    <li>Generate statistics and insights</li>
                    <li>Create charts and visualizations</li>
                    <li>Filter and explore your data</li>
                </ul>
                What would you like to know about your data?
            </div>
        </div>
        
        <div class="chat-input-container">
            <div class="input-group">
                <input 
                    type="text" 
                    class="form-control chat-input" 
                    id="messageInput"
                    placeholder="Ask me about your data..." 
                    onkeypress="handleKeyPress(event)"
                >
                <button class="send-button ms-2" onclick="sendMessage()">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            addUserMessage(message);
            
            // Clear input
            input.value = '';
            
            // Show AI thinking
            showAIThinking();
            
            // Send to backend
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                hideAIThinking();
                
                if (data.success) {
                    addAIMessage(data.ai_response, data.tool_result, data.tool_used);
                } else {
                    addAIMessage('Sorry, I encountered an error: ' + data.error);
                }
            })
            .catch(error => {
                hideAIThinking();
                addAIMessage('Sorry, I encountered a connection error. Please try again.');
                console.error('Error:', error);
            });
        }

        function addUserMessage(message) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message user-message';
            messageDiv.innerHTML = `<i class="fas fa-user"></i> <strong>You:</strong> ${escapeHtml(message)}`;
            chatMessages.appendChild(messageDiv);
            scrollToBottom();
        }

        function addAIMessage(response, toolResult = null, toolUsed = null) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ai-message';
            
            let content = `<i class="fas fa-robot"></i> <strong>AI:</strong> ${escapeHtml(response)}`;
            
            if (toolUsed && toolResult) {
                content += `<div class="tool-result"><strong>Tool used:</strong> ${escapeHtml(toolUsed)}<br><strong>Result:</strong><br>${escapeHtml(toolResult)}</div>`;
            }
            
            messageDiv.innerHTML = content;
            chatMessages.appendChild(messageDiv);
            scrollToBottom();
        }

        function showAIThinking() {
            const chatMessages = document.getElementById('chatMessages');
            const thinkingDiv = document.createElement('div');
            thinkingDiv.id = 'thinkingIndicator';
            thinkingDiv.className = 'message ai-message typing-indicator';
            thinkingDiv.innerHTML = `
                <i class="fas fa-robot"></i> <strong>AI:</strong> Thinking
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            `;
            chatMessages.appendChild(thinkingDiv);
            scrollToBottom();
        }

        function hideAIThinking() {
            const thinkingIndicator = document.getElementById('thinkingIndicator');
            if (thinkingIndicator) {
                thinkingIndicator.remove();
            }
        }

        function scrollToBottom() {
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Focus on input when page loads
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('messageInput').focus();
        });
    </script>
</body>
</html>"""
    
    with open(templates_dir / "chat.html", "w") as f:
        f.write(chat_html)

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
