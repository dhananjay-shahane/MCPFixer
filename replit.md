# Overview

This is an MCP (Model Context Protocol) Data Analysis System that provides tools for analyzing CSV data through multiple interfaces. The system offers both programmatic access through an MCP server and a web-based dashboard for interactive data exploration. It integrates with Ollama for natural language querying and provides comprehensive data analysis capabilities including statistics generation, data filtering, and chart creation.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Application Structure
The system follows a modular architecture with clear separation between server logic, client interfaces, and web components:

- **Server Module**: Contains the core MCP server implementation using FastMCP framework
- **Client Module**: Provides multiple client interfaces (direct client, Ollama integration, CLI)
- **Web Interface**: Flask-based web application for browser-based interaction
- **Scripts**: Entry points for running server and client components

## Data Processing Framework
The system uses pandas as the primary data processing engine, with matplotlib for visualization generation. Data files are stored in a dedicated `data/` directory, and generated outputs (charts, filtered data) are saved to an `output/` directory.

## Tool Architecture
Core functionality is implemented as MCP tools that can be called through various interfaces:

- **read_csv**: Loads and displays CSV file contents
- **get_data_stats**: Generates comprehensive statistical summaries
- **get_column_info**: Provides detailed column analysis
- **filter_data**: Applies filtering operations with multiple comparison operators
- **generate_chart**: Creates visualizations (bar, line, scatter, pie charts)

## Client Interface Design
Multiple client interfaces support different use cases:

- **DirectClient**: Bypasses MCP protocol for direct function calls
- **OllamaClient**: Enables natural language queries through LLM integration
- **CLI Interface**: Command-line tool with Ollama connectivity checks
- **Web Dashboard**: Browser-based interface with file upload and interactive analysis

## Communication Protocols
The system supports both stdio-based MCP communication for programmatic access and HTTP-based Flask endpoints for web interface interactions. The architecture allows for seamless switching between different communication methods.

# External Dependencies

## Core Libraries
- **FastMCP**: Framework for implementing MCP server functionality
- **pandas**: Data manipulation and analysis library
- **matplotlib**: Plotting and visualization library
- **numpy**: Numerical computing support
- **Flask**: Web framework for dashboard interface

## AI Integration
- **Ollama**: Local LLM service for natural language query processing
- **requests**: HTTP client for Ollama API communication

## System Dependencies
- **psutil**: Process monitoring for Ollama service detection
- **argparse**: Command-line argument parsing
- **pathlib**: Modern path handling utilities

## Frontend Components
- **Bootstrap 5.1.3**: CSS framework for responsive web interface
- **Font Awesome 6.0.0**: Icon library for UI elements

## Development Tools
The system is designed to work with standard Python development tools and includes comprehensive error handling for missing dependencies or services.