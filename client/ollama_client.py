import requests
import json
import time
import os
from typing import Optional, Dict, Any

class OllamaClient:
    """Client for interacting with Ollama LLM for natural language data analysis queries"""
    
    def __init__(self, model="llama3.2", base_url="http://localhost:11434", max_retries=3):
        self.model = model
        # Check for external Ollama URL in environment
        self.base_url = os.getenv("OLLAMA_URL", base_url)
        self.max_retries = max_retries
        self.system_prompt = """You are a helpful AI assistant that helps users analyze data using specialized tools.

Available tools:
1. read_csv(filename) - Read CSV file content from data directory
2. get_data_stats(data_source) - Get comprehensive statistics about CSV data
3. get_column_info(data_source, column=None) - Get detailed information about columns
4. filter_data(data_source, column, value, operation="equals") - Filter data by column value
5. generate_chart(data_source, chart_type="bar", title="Chart", x_axis="x", y_axis="y") - Create visualizations

When a user asks about data analysis, respond with a JSON object containing:
{
    "tool": "tool_name",
    "parameters": {param1: value1, param2: value2, ...},
    "explanation": "Brief explanation of why you chose this tool and what it will do"
}

If the request is unclear or doesn't match any tool, respond with:
{
    "tool": null,
    "parameters": {},
    "explanation": "Your helpful explanation or clarification request"
}

Examples:
- "Show me the statistics for data.csv" → {"tool": "get_data_stats", "parameters": {"data_source": "data.csv"}, "explanation": "Getting comprehensive statistics for the dataset"}
- "Create a bar chart of sales by month" → {"tool": "generate_chart", "parameters": {"data_source": "sales.csv", "chart_type": "bar", "title": "Sales by Month", "x_axis": "month", "y_axis": "sales"}, "explanation": "Creating a bar chart visualization"}
"""

    def process_query(self, query):
        """Process natural language query using Ollama with retries"""
        for attempt in range(self.max_retries):
            try:
                print("AI: Analyzing your request...", end="", flush=True)
                
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": query}
                        ],
                        "stream": False
                    },
                    timeout=30
                )
                
                print("\r" + " " * 50 + "\r", end="", flush=True)
                
                if response.status_code == 200:
                    content = response.json().get('message', {}).get('content', '')
                    
                    # Try to extract JSON from response
                    try:
                        # Look for JSON in the response
                        start_idx = content.find('{')
                        end_idx = content.rfind('}') + 1
                        
                        if start_idx != -1 and end_idx != 0:
                            json_str = content[start_idx:end_idx]
                            return json.loads(json_str)
                        else:
                            # If no JSON found, return it as explanation
                            return {
                                "tool": None,
                                "parameters": {},
                                "explanation": content
                            }
                    except json.JSONDecodeError:
                        # If JSON parsing fails, return as explanation
                        return {
                            "tool": None,
                            "parameters": {},
                            "explanation": content
                        }
                else:
                    return {
                        "tool": None,
                        "parameters": {},
                        "explanation": f"Ollama API error: {response.status_code}"
                    }
                    
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    print(f"\rAttempt {attempt + 1} timed out, retrying...")
                    time.sleep(2)
                else:
                    return {
                        "tool": None,
                        "parameters": {},
                        "explanation": f"Request timed out after {self.max_retries} attempts. The model might be too large for your system."
                    }
            except requests.exceptions.ConnectionError:
                return {
                    "tool": None,
                    "parameters": {},
                    "explanation": "Cannot connect to Ollama. Please make sure it's running with 'ollama serve'"
                }
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"\rAttempt {attempt + 1} failed, retrying...")
                    time.sleep(2)
                else:
                    return {
                        "tool": None,
                        "parameters": {},
                        "explanation": f"Error processing query: {str(e)}"
                    }

def main(port=11434, model="llama3.2"):
    """Interactive main function for Ollama client"""
    try:
        from client.direct_client import DirectClient
    except ImportError:
        print("Error: Could not import DirectClient")
        return
    
    # Initialize clients
    ollama_client = OllamaClient(
        base_url=f"http://localhost:{port}", 
        model=model
    )
    direct_client = DirectClient()
    
    print("🤖 MCP Data Analysis Assistant")
    print("=" * 50)
    print(f"Using Ollama model: {model} on port {port}")
    print("Type your data analysis questions in natural language")
    print("Available commands:")
    print("  'help' - Show available tools")
    print("  'files' - List available data files")
    print("  'quit' - Exit")
    print()
    
    # Show available data files
    data_files = direct_client.list_data_files()
    if data_files:
        print(f"📁 Available data files: {', '.join(data_files)}")
    else:
        print("📁 No CSV files found in data directory")
        print("   Add CSV files to the 'data' directory to get started")
    print()
    
    while True:
        try:
            user_input = input("🧑 You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'help':
                tools = direct_client.list_tools()
                print("🔧 Available tools:")
                for name, desc in tools.items():
                    print(f"   {name}: {desc}")
                continue
            elif user_input.lower() == 'files':
                data_files = direct_client.list_data_files()
                if data_files:
                    print(f"📁 CSV files: {', '.join(data_files)}")
                else:
                    print("📁 No CSV files found in data directory")
                continue
            
            # Process query with Ollama
            response = ollama_client.process_query(user_input)
            
            if response and "tool" in response:
                if response["tool"]:
                    print(f"🤖 AI: I'll use the '{response['tool']}' tool")
                    print(f"💭 Reasoning: {response['explanation']}")
                    
                    # Execute the tool using direct client
                    print("⚙️  Executing...")
                    try:
                        result = direct_client.execute_tool(
                            response["tool"], 
                            response["parameters"]
                        )
                        
                        print("📊 Result:")
                        print(result)
                        
                    except Exception as e:
                        print(f"❌ Error executing tool: {str(e)}")
                else:
                    print(f"🤖 AI: {response['explanation']}")
            else:
                print("🤖 AI: Sorry, I couldn't process your request.")
                    
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
