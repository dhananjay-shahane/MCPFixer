#!/usr/bin/env python3
"""
Pie Chart Generator Script
Creates pie charts from CSV data and saves as PNG with timestamp
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys
import argparse

def generate_pie_chart(csv_file, label_column, value_column, title=None, output_dir="output"):
    """
    Generate a pie chart from CSV data
    
    Args:
        csv_file: Path to CSV file
        label_column: Column name for pie slice labels
        value_column: Column name for pie slice values
        title: Chart title
        output_dir: Directory to save output
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Read CSV data
        df = pd.read_csv(csv_file)
        
        # Validate columns exist
        if label_column not in df.columns:
            raise ValueError(f"Column '{label_column}' not found. Available columns: {list(df.columns)}")
        if value_column not in df.columns:
            raise ValueError(f"Column '{value_column}' not found. Available columns: {list(df.columns)}")
        
        # Create pie chart
        plt.figure(figsize=(10, 8))
        
        # Group by label column and sum values if there are duplicates
        grouped_data = df.groupby(label_column)[value_column].sum()
        
        # Create pie chart
        plt.pie(grouped_data.values, labels=grouped_data.index, autopct='%1.1f%%', startangle=90)
        
        if title:
            plt.title(title)
        else:
            plt.title(f'Pie Chart: {value_column} by {label_column}')
        
        plt.axis('equal')
        
        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_dir}/pie_chart_{timestamp}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_file
        
    except Exception as e:
        return f"Error generating pie chart: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='Generate pie chart from CSV data')
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('label_column', help='Column name for pie slice labels')
    parser.add_argument('value_column', help='Column name for pie slice values')
    parser.add_argument('--title', help='Chart title')
    parser.add_argument('--output', default='output', help='Output directory')
    
    args = parser.parse_args()
    
    result = generate_pie_chart(args.csv_file, args.label_column, args.value_column, args.title, args.output)
    print(result)

if __name__ == "__main__":
    main()