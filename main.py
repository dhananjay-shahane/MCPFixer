#!/usr/bin/env python3
"""
Main entry point for MCP Data Analysis System
"""

import sys
import argparse
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def run_server():
    """Run the MCP server"""
    try:
        from scripts.run_server import main as server_main
        return server_main()
    except Exception as e:
        print(f"Error running server: {e}")
        return 1

def run_client():
    """Run the MCP client"""
    try:
        from scripts.run_client import main as client_main
        return client_main()
    except Exception as e:
        print(f"Error running client: {e}")
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="MCP Data Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py server          # Start MCP server
  python main.py client          # Start interactive client
  python main.py client --help   # Show client options
        """
    )
    
    parser.add_argument(
        'component', 
        choices=['server', 'client'],
        help='Component to run (server or client)'
    )
    
    # Parse known args to allow client-specific arguments to pass through
    args, remaining = parser.parse_known_args()
    
    if args.component == 'server':
        # Pass any remaining arguments to the server
        sys.argv = [sys.argv[0]] + remaining
        return run_server()
    elif args.component == 'client':
        # Pass any remaining arguments to the client
        sys.argv = [sys.argv[0]] + remaining
        return run_client()

if __name__ == "__main__":
    exit(main())
