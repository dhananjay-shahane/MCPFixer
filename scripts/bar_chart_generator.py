#!/usr/bin/env python3
"""
Bar Chart Generator Script
Creates bar charts from CSV data and saves as PNG with timestamp
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys
import argparse

def generate_bar_chart(csv_file, x_column, y_column, title=None, output_dir="output"):
    """
    Generate a bar chart from CSV data
    
    Args:
        csv_file: Path to CSV file
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        title: Chart title
        output_dir: Directory to save output
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Read CSV data
        df = pd.read_csv(csv_file)
        
        # Validate columns exist
        if x_column not in df.columns:
            raise ValueError(f"Column '{x_column}' not found. Available columns: {list(df.columns)}")
        if y_column not in df.columns:
            raise ValueError(f"Column '{y_column}' not found. Available columns: {list(df.columns)}")
        
        # Create bar chart
        plt.figure(figsize=(12, 8))
        plt.bar(df[x_column], df[y_column])
        plt.xlabel(x_column)
        plt.ylabel(y_column)
        
        if title:
            plt.title(title)
        else:
            plt.title(f'Bar Chart: {y_column} by {x_column}')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_dir}/bar_chart_{timestamp}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_file
        
    except Exception as e:
        return f"Error generating bar chart: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='Generate bar chart from CSV data')
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('x_column', help='Column name for x-axis')
    parser.add_argument('y_column', help='Column name for y-axis')
    parser.add_argument('--title', help='Chart title')
    parser.add_argument('--output', default='output', help='Output directory')
    
    args = parser.parse_args()
    
    result = generate_bar_chart(args.csv_file, args.x_column, args.y_column, args.title, args.output)
    print(result)

if __name__ == "__main__":
    main()