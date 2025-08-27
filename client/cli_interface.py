import argparse
import requests
import time
import json
import sys
import os
import subprocess
from typing import Optional, Dict, Any

def check_ollama(port=11434):
    """Check if Ollama is running on the specified port"""
    try:
        response = requests.get(f"http://localhost:{port}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            if models.get('models'):
                return True, port
            else:
                print("Warning: No models found. Please pull a model with: ollama pull llama3.2")
                return False, port
        else:
            print(f"Ollama responded with status code: {response.status_code}")
            return False, port
    except requests.ConnectionError:
        # Try alternative ports
        for alt_port in [11435, 11436, 11437]:
            try:
                response = requests.get(f"http://localhost:{alt_port}/api/tags", timeout=3)
                if response.status_code == 200:
                    print(f"Found Ollama running on port {alt_port}")
                    return True, alt_port
            except:
                continue
        print("Error: Could not connect to Ollama. Please make sure it's running.")
        print("You can start it with: ollama serve")
        return False, port
    except Exception as e:
        print(f"Error checking Ollama: {str(e)}")
        return False, port

def is_ollama_process_running():
    """Check if Ollama process is already running"""
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['tasklist', '/fi', 'imagename eq ollama.exe'], 
                                  capture_output=True, text=True)
            return "ollama.exe" in result.stdout
        else:  # Unix-like systems
            try:
                import psutil
                for proc in psutil.process_iter(['name']):
                    if 'ollama' in proc.info['name'].lower():
                        return True
                return False
            except ImportError:
                # Fallback to ps command
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                return 'ollama' in result.stdout.lower()
    except:
        return False

def run_ollama_query(query: str, port: int = 11434, model: str = "llama3.2") -> Optional[Dict[str, Any]]:
    """Run a query through Ollama and return the response"""
    try:
        print("AI: Thinking...", end="", flush=True)
        
        response = requests.post(
            f"http://localhost:{port}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant that helps users work with data analysis tools."},
                    {"role": "user", "content": query}
                ],
                "stream": False
            },
            timeout=30
        )
        
        print("\r" + " " * 50 + "\r", end="", flush=True)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ollama API error: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        print("\rAI: Request timed out. The model might be too large for your system.")
        print("Try using a smaller model: ollama pull llama3.2:1b")
        return None
    except Exception as e:
        print(f"\rError running query: {str(e)}")
        return None

def run_direct_tool(tool_name: str, params: Dict[str, Any]):
    """Execute a tool directly without Ollama"""
    try:
        from client.direct_client import DirectClient
        client = DirectClient()
        result = client.execute_tool(tool_name, params)
        return result
    except ImportError as e:
        return f"Direct client not available: {e}"
    except Exception as e:
        return f"Error executing tool: {str(e)}"

def start_ollama():
    """Try to start Ollama service"""
    try:
        print("Starting Ollama...")
        process = subprocess.Popen(
            ["ollama", "serve"], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Wait and check if Ollama started successfully
        for i in range(15):
            time.sleep(1)
            ollama_running, port = check_ollama()
            if ollama_running:
                print("Ollama started successfully!")
                return True, port
            print(f"Waiting for Ollama to start... ({i+1}/15)")
        
        print("Ollama still not responding after 15 seconds.")
        return False, 11434
        
    except FileNotFoundError:
        print("Ollama command not found. Please install Ollama first.")
        print("Visit: https://ollama.ai")
        return False, 11434
    except Exception as e:
        print(f"Failed to start Ollama: {str(e)}")
        return False, 11434

def run_cli():
    parser = argparse.ArgumentParser(description="MCP Data Analysis Client CLI")
    parser.add_argument('--query', help='Natural language query for data analysis')
    parser.add_argument('--tool', help='Direct tool execution (bypass LLM)')
    parser.add_argument('--params', help='Tool parameters as JSON string')
    parser.add_argument('--model', help='Ollama model to use', default='llama3.2')
    parser.add_argument('--interactive', action='store_true', help='Start interactive mode')
    parser.add_argument('--list-tools', action='store_true', help='List available tools')
    
    args = parser.parse_args()
    
    # List available tools
    if args.list_tools:
        print("Available tools:")
        print("1. read_csv - Read CSV file content")
        print("2. get_data_stats - Get comprehensive statistics about CSV data")
        print("3. get_column_info - Get detailed information about columns")
        print("4. filter_data - Filter CSV data by column value")
        print("5. generate_chart - Generate charts from CSV data")
        return
    
    # Direct tool execution
    if args.tool:
        try:
            params = json.loads(args.params) if args.params else {}
            result = run_direct_tool(args.tool, params)
            print(f"Tool result: {result}")
        except json.JSONDecodeError:
            print("Error: Invalid JSON in --params argument")
        return
    
    # Check if Ollama is needed
    if args.query or args.interactive:
        ollama_running, port = check_ollama()
        
        if not ollama_running:
            if is_ollama_process_running():
                print("Ollama process is running but not responding. It might be stuck.")
                restart = input("Would you like to try restarting Ollama? (y/n): ")
                if restart.lower() == 'y':
                    try:
                        if os.name == 'nt':  # Windows
                            subprocess.run(['taskkill', '/f', '/im', 'ollama.exe'], 
                                          capture_output=True)
                        else:
                            subprocess.run(['pkill', 'ollama'], capture_output=True)
                        time.sleep(2)
                    except:
                        pass
                else:
                    print("Using direct tool mode instead...")
                    return
            
            start = input("Would you like to start Ollama now? (y/n): ")
            if start.lower() == 'y':
                success, port = start_ollama()
                if not success:
                    print("Failed to start Ollama. Using direct tool mode instead.")
                    return
            else:
                print("Ollama is required for natural language queries.")
                print("You can use direct tool execution with --tool and --params arguments.")
                return
    
    # Single query mode
    if args.query:
        response = run_ollama_query(args.query, port, args.model)
        if response:
            message_content = response.get('message', {}).get('content', 'No response generated')
            print(f"AI: {message_content}")
        return
    
    # Interactive mode
    if args.interactive:
        try:
            from client.ollama_client import main
            main(port, args.model)
        except ImportError:
            print("Interactive client not available. Falling back to simple mode...")
            interactive_fallback(port, args.model)
    else:
        # Default: start interactive mode
        try:
            from client.ollama_client import main
            main(port, args.model)
        except ImportError:
            interactive_fallback(port, args.model)

def interactive_fallback(port, model):
    """Fallback interactive mode"""
    print(f"MCP Data Analysis Client - Interactive Mode")
    print(f"Using model: {model}")
    print("Type 'quit', 'exit', or 'q' to quit")
    print("Type 'help' for available commands")
    
    while True:
        try:
            query = input("\nUser: ")
            if query.lower() in ['quit', 'exit', 'q']:
                break
            elif query.lower() == 'help':
                print("Commands:")
                print("- Ask natural language questions about data analysis")
                print("- 'tools' - List available tools")
                print("- 'quit' - Exit the program")
                continue
            elif query.lower() == 'tools':
                print("Available tools: read_csv, get_data_stats, get_column_info, filter_data, generate_chart")
                continue
            
            response = run_ollama_query(query, port, model)
            if response:
                message_content = response.get('message', {}).get('content', 'No response generated')
                print(f"AI: {message_content}")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    run_cli()
