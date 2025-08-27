#!/usr/bin/env python3
"""
Data Analyzer Script
Provides comprehensive analysis of CSV data
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys
import argparse
import json

def analyze_data(csv_file, output_dir="output"):
    """
    Perform comprehensive analysis of CSV data
    
    Args:
        csv_file: Path to CSV file
        output_dir: Directory to save output
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Read CSV data
        df = pd.read_csv(csv_file)
        
        # Basic info
        analysis = {
            "file_info": {
                "filename": os.path.basename(csv_file),
                "shape": df.shape,
                "size_mb": round(os.path.getsize(csv_file) / (1024*1024), 4)
            },
            "columns": list(df.columns),
            "data_types": df.dtypes.astype(str).to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "null_percentages": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
        }
        
        # Statistical summary for numerical columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            analysis["numeric_summary"] = df[numeric_cols].describe().to_dict()
        
        # Value counts for categorical columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        analysis["categorical_info"] = {}
        for col in categorical_cols:
            if df[col].nunique() <= 20:  # Only for columns with reasonable unique values
                analysis["categorical_info"][col] = df[col].value_counts().head(10).to_dict()
        
        # Save analysis as JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_file = f"{output_dir}/data_analysis_{timestamp}.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        return analysis_file, analysis
        
    except Exception as e:
        return None, f"Error analyzing data: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='Analyze CSV data')
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('--output', default='output', help='Output directory')
    
    args = parser.parse_args()
    
    analysis_file, result = analyze_data(args.csv_file, args.output)
    
    if analysis_file:
        print(f"Analysis saved to: {analysis_file}")
        print("\nSummary:")
        print(json.dumps(result, indent=2))
    else:
        print(result)

if __name__ == "__main__":
    main()