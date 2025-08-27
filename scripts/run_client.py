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
    """Client functionality has been integrated into the web interface"""
    print("MCP Data Analysis Client")
    print("The client functionality is now integrated into the web interface.")
    print("Please use the web application at http://localhost:5000")
    print("Run 'python app.py' to start the web server.")
    return 0

if __name__ == "__main__":
    exit(main())
