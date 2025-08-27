import sys
import os
import json
from typing import Dict, Any, Optional

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class DirectClient:
    """Direct client for executing MCP server tools without going through the MCP protocol"""
    
    def __init__(self):
        # Import the actual functions from the server module
        try:
            from server.server import (
                generate_chart, 
                get_data_stats, 
                filter_data, 
                read_csv,
                get_column_info
            )
            
            self.available_tools = {
                "generate_chart": generate_chart,
                "get_data_stats": get_data_stats,
                "filter_data": filter_data,
                "read_csv": read_csv,
                "get_column_info": get_column_info
            }
        except ImportError as e:
            print(f"Error importing server tools: {e}")
            self.available_tools = {}
    
    def list_tools(self) -> Dict[str, str]:
        """Get a list of available tools with descriptions"""
        return {
            "read_csv": "Read CSV file content from data directory",
            "get_data_stats": "Get comprehensive statistics about CSV data",
            "get_column_info": "Get detailed information about columns in dataset",
            "filter_data": "Filter CSV data by column value with various operations",
            "generate_chart": "Generate charts from CSV data (bar, line, scatter, pie)"
        }
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
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
            return result
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
            user_input = input("direct> ").strip()
            if not user_input:
                continue
                
            parts = user_input.split(None, 1)
            command = parts[0].lower()
            
            if command in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            elif command == 'help':
                print("Commands:")
                print("  tools - List available tools")
                print("  info <tool_name> - Get detailed tool information")
                print("  files - List CSV files in data directory")
                print("  exec <tool_name> <params_json> - Execute tool with JSON parameters")
                print("  quit - Exit")
            elif command == 'tools':
                tools = client.list_tools()
                for name, desc in tools.items():
                    print(f"  {name}: {desc}")
            elif command == 'files':
                data_files = client.list_data_files()
                if data_files:
                    print(f"CSV files in data directory: {', '.join(data_files)}")
                else:
                    print("No CSV files found in data directory")
            elif command == 'info':
                if len(parts) < 2:
                    print("Usage: info <tool_name>")
                    continue
                tool_name = parts[1]
                info = client.get_tool_info(tool_name)
                if info:
                    print(f"Tool: {tool_name}")
                    print(f"Description: {info['description']}")
                    print("Parameters:")
                    for param, desc in info['parameters'].items():
                        print(f"  {param}: {desc}")
                    print(f"Example: {json.dumps(info['example'], indent=2)}")
                else:
                    print(f"Tool '{tool_name}' not found")
            elif command == 'exec':
                if len(parts) < 2:
                    print("Usage: exec <tool_name> <params_json>")
                    print("Example: exec get_data_stats {\"data_source\": \"sample_data.csv\"}")
                    continue
                
                exec_parts = parts[1].split(None, 1)
                if len(exec_parts) < 2:
                    print("Usage: exec <tool_name> <params_json>")
                    continue
                
                tool_name = exec_parts[0]
                try:
                    params = json.loads(exec_parts[1])
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON parameters: {e}")
                    continue
                
                print(f"Executing {tool_name}...")
                result = client.execute_tool(tool_name, params)
                print("Result:")
                print(result)
            else:
                print(f"Unknown command: {command}. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
