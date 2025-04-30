#!/usr/bin/env python3
import re
import os
import sys
import argparse
from tqdm import tqdm
import pandas as pd
import glob
import json

# Directory structure constants
DATA_DIR = "data"
RESULTS_DIR = "results"

def format_phone(number):
    """
    Clean and format a phone number
    
    Args:
        number: The phone number to format
        
    Returns:
        A formatted phone number string or None if invalid
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', str(number))
    
    # If it has exactly 10 digits, format it
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    else:
        return None  # Return None for invalid phone numbers

def process_data(input_pattern=None, output_dir=None):
    """
    Process JSON files from scraping results and generate summary and detail CSVs
    
    Args:
        input_pattern: Glob pattern to find input JSON files
        output_dir: Directory where output CSV files will be saved
    """
    # Create output directory if it doesn't exist
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Use default pattern if none provided
    if not input_pattern:
        input_pattern = os.path.join(DATA_DIR, "*", "raw", "*.json")
    
    # Fix Windows backslashes
    input_pattern = input_pattern.replace("\\", "/")
    
    print(f"Looking for files with pattern: {input_pattern}")
    
    # Find all JSON files
    files = glob.glob(input_pattern)
    
    if not files:
        print(f"No files found matching pattern: {input_pattern}")
        return
    
    print(f"Found {len(files)} files to process")
    
    summary_rows = []
    detail_rows = []

    # Loop through each file
    for file in tqdm(files):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Summary info
                summary_rows.append({
                    'postal_code': data.get('postal_code', 'unknown'),
                    'totalcount': data.get('totalcount', 0)
                })
                
                # Detail info
                if data.get('results'):  # Only if there are results
                    detail_rows.extend(data['results'])
        except Exception as e:
            print(f"Error processing file {file}: {e}")
            continue

    # Create the two DataFrames
    summary_df = pd.DataFrame(summary_rows)
    
    if not detail_rows:
        print("No detail records found")
        detail_df = pd.DataFrame()
    else:
        detail_df = pd.DataFrame(detail_rows)
        if 'cpsonumber' in detail_df.columns:
            detail_df = detail_df.drop_duplicates(subset=['cpsonumber'])
        
        # Apply phone formatting
        if 'phonenumber' in detail_df.columns:
            detail_df['phonenumber'] = detail_df['phonenumber'].apply(format_phone)
        if 'fax' in detail_df.columns:
            detail_df['fax'] = detail_df['fax'].apply(format_phone)

    # Find capped codes
    summary_df_capped = summary_df[
        (summary_df['totalcount'] == -1) &
        (summary_df['postal_code'].apply(lambda x: len(str(x)) == 7))
    ]
    
    if not summary_df_capped.empty:
        print(f"Found {len(summary_df_capped)} capped postal codes")
    
    # Determine output file paths
    summary_path = os.path.join(output_dir or RESULTS_DIR, "summary.csv")
    details_path = os.path.join(output_dir or RESULTS_DIR, "details.csv")
    
    # Save to CSVs
    summary_df.to_csv(summary_path, index=False)
    if not detail_df.empty:
        detail_df.to_csv(details_path, index=False)
    
    print(f"Saved summary to: {summary_path}")
    print(f"Saved details to: {details_path}")
    print(f"Processed {len(summary_rows)} postal codes with {len(detail_rows)} doctor records")

def main():
    """Parse command-line arguments and run the processing"""
    parser = argparse.ArgumentParser(description='Create summary and detail CSV outputs from CPSO scrape data')
    
    parser.add_argument('-i', '--input', 
                        help='Glob pattern for input JSON files (e.g., "data/*/raw/*.json")')
    
    parser.add_argument('-o', '--output-dir',
                        help='Directory to save CSV output files')
    
    args = parser.parse_args()
    
    # Process the data with provided arguments
    process_data(input_pattern=args.input, output_dir=args.output_dir)

if __name__ == "__main__":
    main()
