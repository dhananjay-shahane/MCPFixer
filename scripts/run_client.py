#!/usr/bin/env python3
"""
Script to run the MCP Data Analysis Client
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

def main():
    """Run the client CLI interface"""
    try:
        from client.cli_interface import run_cli
        run_cli()
    except ImportError as e:
        print(f"Error importing client: {e}")
        print("Make sure all dependencies are installed")
        return 1
    except Exception as e:
        print(f"Error running client: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
