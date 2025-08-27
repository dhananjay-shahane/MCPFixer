#!/usr/bin/env python3
"""
Script to run the MCP Data Analysis Server
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

def check_directories():
    """Ensure required directories exist"""
    dirs_to_create = ['data', 'output']
    
    for dir_name in dirs_to_create:
        dir_path = parent_dir / dir_name
        if not dir_path.exists():
            print(f"Creating directory: {dir_path}")
            dir_path.mkdir(exist_ok=True)
        else:
            print(f"Directory exists: {dir_path}")

def run_server():
    """Run the MCP server"""
    try:
        # Ensure directories exist
        check_directories()
        
        print("Starting MCP Data Analysis Server...")
        print("Server will communicate via stdio")
        print("Press Ctrl+C to stop")
        print("-" * 50)
        
        # Import and run the server
        from server.server import mcp
        mcp.run(transport='stdio')
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except ImportError as e:
        print(f"Error importing server: {e}")
        print("Make sure all dependencies are installed")
    except Exception as e:
        print(f"Error running server: {e}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run MCP Data Analysis Server")
    parser.add_argument('--check', action='store_true', help='Check server setup')
    
    args = parser.parse_args()
    
    if args.check:
        print("Checking server setup...")
        check_directories()
        
        # Check if server can be imported
        try:
            from server.server import mcp
            print("✅ Server module imported successfully")
            print(f"✅ Server name: {mcp.name}")
        except ImportError as e:
            print(f"❌ Error importing server: {e}")
            return 1
        
        print("✅ Server setup looks good!")
        return 0
    else:
        run_server()

if __name__ == "__main__":
    exit(main())
