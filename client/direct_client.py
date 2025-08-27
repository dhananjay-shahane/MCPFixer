import sys
import os
import json
from typing import Dict, Any, Optional

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class DirectClient:
    """Direct client for executing MCP server tools without going through the MCP protocol"""
    
    def __init__(self):
        # Import server module and access the raw functions
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Import the server to access the actual tool functions
            from server.server import mcp
            
            # Extract the actual functions from the MCP tools
            self.available_tools = {}
            self.mcp_server = mcp
            
            # Import individual functions directly since MCP tool decorator wrapping causes issues
            from server.server import (
                read_csv as _read_csv,
                generate_chart as _generate_chart,
                get_data_stats as _get_data_stats,
                filter_data as _filter_data,
                get_column_info as _get_column_info,
                list_data_files as _list_data_files,
                execute_script as _execute_script
            )
            
            # Map tool names to raw functions (bypassing MCP decorators)
            self.available_tools = {
                "read_csv": _read_csv,
                "generate_chart": _generate_chart,
                "get_data_stats": _get_data_stats,
                "filter_data": _filter_data,
                "get_column_info": _get_column_info,
                "list_data_files": _list_data_files,
                "execute_script": _execute_script
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
                    "args": "Additional arguments (optional)"
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
