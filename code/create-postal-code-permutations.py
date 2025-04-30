#!/usr/bin/env python3
"""
Simplified script to generate postal code permutations for the CPSO registry scraper.
This script contains the core functions to generate different levels of postal code permutations.
"""

import os
import json
import string
from tqdm import tqdm

# Valid characters for Canadian postal codes
VALID_LETTERS = [c for c in string.ascii_uppercase if c not in {'D', 'F', 'I', 'O', 'Q', 'U'}]
VALID_DIGITS = list("0123456789")

def generate_ldu1_permutations(postal_codes):
    """
    Generate postal code permutations with 1 character of LDU (4 characters total)
    
    Args:
        postal_codes: List of 3-character postal code prefixes (FSA)
        
    Returns:
        List of 4-character postal codes (FSA+LDU1)
    """
    all_permutations = []
    for postal_code in tqdm(postal_codes):
        # Fourth position: Number
        all_permutations.extend([postal_code + "+" + d for d in VALID_DIGITS])
    
    return all_permutations

def generate_ldu2_permutations(postal_codes):
    """
    Generate postal code permutations with 2 characters of LDU (5 characters total)
    
    Args:
        postal_codes: List of 4-character postal codes (FSA+LDU1)
        
    Returns:
        List of 5-character postal codes (FSA+LDU2)
    """
    all_permutations = []
    for postal_code in tqdm(postal_codes):
        # Fifth position: Letter
        all_permutations.extend([postal_code + l for l in VALID_LETTERS])
    
    return all_permutations

def generate_ldu3_permutations(postal_codes):
    """
    Generate postal code permutations with 3 characters of LDU (full postal code)
    
    Args:
        postal_codes: List of 5-character postal codes (FSA+LDU2)
        
    Returns:
        List of 6-character postal codes (full postal code)
    """
    all_permutations = []
    for postal_code in tqdm(postal_codes):
        # Sixth position: Number
        all_permutations.extend([postal_code + d for d in VALID_DIGITS])
    
    return all_permutations

def save_permutations(permutations, output_file):
    """
    Save postal code permutations to a JSON file
    
    Args:
        permutations: List of postal code permutations
        output_file: Path to the output JSON file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(permutations, f)
        print(f"Saved {len(permutations)} permutations to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving permutations: {e}")
        return False

def generate_and_save_permutations(postal_codes, level, output_dir="data/search-criteria"):
    """
    Generate permutations for the specified level and save to a file
    
    Args:
        postal_codes: List of postal codes to generate permutations from
        level: Permutation level ('ldu1', 'ldu2', or 'ldu3')
        output_dir: Directory to save the output file
        
    Returns:
        List of generated permutations
    """
    if level.lower() == 'ldu1':
        permutations = generate_ldu1_permutations(postal_codes)
        filename = "FSA_LDU1.json"
    elif level.lower() == 'ldu2':
        permutations = generate_ldu2_permutations(postal_codes)
        filename = "FSA_LDU2.json"
    elif level.lower() == 'ldu3':
        permutations = generate_ldu3_permutations(postal_codes)
        filename = "FSA_LDU3.json"
    else:
        raise ValueError(f"Invalid level: {level}. Must be 'ldu1', 'ldu2', or 'ldu3'.")
    
    output_file = os.path.join(output_dir, filename)
    save_permutations(permutations, output_file)
    
    return permutations

def load_postal_codes(input_file):
    """
    Load postal codes from an input file (JSON or CSV)
    Filters to only include postal_codes with totalcount = -1
    
    Args:
        input_file: Path to the input file (JSON or CSV)
        
    Returns:
        List of postal codes where totalcount = -1
    """
    import pandas as pd
    
    try:
        if input_file.endswith('.json'):
            with open(input_file, 'r') as f:
                data = json.load(f)
                # If JSON format contains totalcount, filter accordingly
                postal_codes = []
                for item in data:
                    if isinstance(item, dict) and item.get('totalcount') == -1:
                        postal_codes.append(item.get('postal_code'))
                    else:
                        postal_codes = data  # If simple list format, use as is
        elif input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
            if 'postal_code' in df.columns and 'totalcount' in df.columns:
                # Filter to rows where totalcount is -1
                filtered_df = df[df['totalcount'] == -1]
                postal_codes = filtered_df['postal_code'].tolist()
            else:
                # Fallback if totalcount column doesn't exist
                print("Warning: 'totalcount' column not found, using all postal codes")
                if 'postal_code' in df.columns:
                    postal_codes = df['postal_code'].tolist()
                else:
                    # Use the first column if 'postal_code' doesn't exist
                    postal_codes = df.iloc[:, 0].tolist()
        else:
            raise ValueError(f"Unsupported file format: {input_file}. Must be .json or .csv")
        
        print(f"Loaded {len(postal_codes)} postal codes with totalcount = -1 from {input_file}")
        return postal_codes
    except Exception as e:
        print(f"Error loading input file {input_file}: {e}")
        return []

if __name__ == "__main__":
    import argparse
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Generate postal code permutations for CPSO scraper')
    parser.add_argument('level', type=int, choices=[1, 2, 3], 
                        help='LDU level to generate (1=4th char, 2=5th char, 3=6th char)')
    parser.add_argument('--input_file', default='results/summary.csv',
                        help='Path to input file containing postal codes (JSON or CSV)')
    parser.add_argument('--output-dir', default='data/search-criteria',
                        help='Directory to save output files (default: data/search-criteria)')
    
    args = parser.parse_args()
    
    # Load postal codes from input file
    postal_codes = load_postal_codes(args.input_file)
    
    if not postal_codes:
        print("No postal codes loaded. Exiting.")
        import sys
        sys.exit(1)
    
    # Filter postal codes by the required length for each level
    # Level 1 requires 3-character inputs (FSA)
    # Level 2 requires 4-character inputs (FSA+LDU1)
    # Level 3 requires 5-character inputs (FSA+LDU2)
    required_length_map = {1: 3, 2: 4, 3: 5}
    required_length = required_length_map[args.level]
    
    # Filter postal codes by their true length (excluding '+' characters)
    filtered_postal_codes = []
    for code in postal_codes:
        # Remove '+' characters when calculating length
        actual_length = len(code.replace('+', ''))
        if actual_length == required_length:
            filtered_postal_codes.append(code)
    
    postal_codes = filtered_postal_codes
    
    print(f"Filtered to {len(postal_codes)} postal codes with length {required_length} (excluding '+' characters)")
    
    if not postal_codes:
        print("No valid postal codes after filtering.  All searches worked. Exiting.")
        import sys
        sys.exit(1)
    
    # Convert level number to string format used by generate_and_save_permutations
    level_map = {1: 'ldu1', 2: 'ldu2', 3: 'ldu3'}
    level = level_map[args.level]
    
    # Generate and save permutations
    permutations = generate_and_save_permutations(
        postal_codes,
        level,
        args.output_dir
    )
    
    print(f"Generated {len(permutations)} permutations for LDU level {args.level}")