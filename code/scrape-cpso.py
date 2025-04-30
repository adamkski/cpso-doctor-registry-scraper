import os
import json
import requests
import time
import random
import sys
import argparse
from pathlib import Path

def fetch_results_with_rate_limit(postal_codes, doctor_type="Any", last_name="Any", delay_range=(2, 5), output_dir="data"):
    """
    Fetch results from CPSO registry with rate limiting
    
    Args:
        postal_codes: List of postal codes to search
        doctor_type: Type of doctor to search for ("Any", "Family+Doctor", "Specialist")
        last_name: Last name to filter by ("Any" ignores this field)
        delay_range: Tuple defining min and max delay between requests
        output_dir: Directory to save results
        
    Returns:
        List of result data
    """
    all_results = []
    
    for postal_code in postal_codes:
        # Random delay between requests
        delay = random.uniform(delay_range[0], delay_range[1])
        time.sleep(delay)
        
        print(f"Fetching results for postal code={postal_code}; physician type={doctor_type}; last name={last_name}...")

        url = "https://register.cpso.on.ca/Get-Search-Results/"

        headers = {
            "accept": "*/*",
            "accept-language": "fr-CA,fr;q=0.9,en-CA;q=0.8,en-US;q=0.7,en;q=0.6",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-requested-with": "XMLHttpRequest",
            "User-Agent": "CPSO Registry Scraper (+https://github.com/yourusername/cpso-doctor-registry-scraper)"
        }

        if doctor_type == "Any":
            body = "cbx-includeinactive=on&postalCode={}&doctorType={}".format(postal_code, doctor_type)
        elif (doctor_type == "Family+Doctor") & (last_name == "Any"):
            body = "cbx-includeinactive=on&postalCode={}&doctorType={}".format(postal_code, doctor_type)
        elif (doctor_type == "Specialist") & (last_name == "Any"):
            body = "cbx-includeinactive=on&postalCode={}&doctorType={}&SpecialistType={}".format(postal_code, doctor_type, "Psychiatry")
        elif (doctor_type == "Family+Doctor") & (last_name != "Any"):
            body = "cbx-includeinactive=on&lastName={}&postalCode={}&doctorType={}".format(last_name, postal_code, doctor_type)
        elif (doctor_type == "Specialist") & (last_name != "Any"):
            body = "cbx-includeinactive=on&lastName={}&postalCode={}&doctorType={}&SpecialistType={}".format(last_name, postal_code, doctor_type, "Psychiatry")

        session = requests.Session()
        session.get("https://register.cpso.on.ca/Advanced-Search/")

        result_data = fetch_with_backoff(url, body, headers, session)
        
        if result_data:
            # Add the postal code to the top level of the JSON
            result_data["postal_code"] = postal_code
            all_results.append(result_data)
            print(f"Retrieved {len(result_data.get('results', []))} results for {postal_code}+{doctor_type}+{last_name}")

            # Ensure output directory exists
            os.makedirs(os.path.join(output_dir, "raw"), exist_ok=True)
            
            # Save results to file
            filename = os.path.join(output_dir, "raw", f"{postal_code}+{doctor_type}+{last_name}.json")
            save_results_to_file(result_data, filename=filename)
    
    return all_results

def fetch_with_backoff(url, body, headers, session, max_retries=5, initial_delay=2):
    """Make a request with exponential backoff for rate limiting"""
    retries = 0
    delay = initial_delay
    
    while retries < max_retries:
        try:
            # Use allow_redirects=True to follow any redirects
            # Use cookies=True to maintain session cookies
            response = session.post(
                url, 
                headers=headers, 
                data=body, 
                allow_redirects=True,
                cookies=requests.cookies.RequestsCookieJar()  # Initialize an empty cookie jar
            )
                        
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Too Many Requests
                print(f"Rate limited. Backing off for {delay} seconds...")
            else:
                print(f"Error: Status code {response.status_code}")
        except Exception as e:
            print(f"Request failed: {e}")

            # If you only want to continue for the specific error
            if "Invalid control character at: line" in str(e):
                print("Skipping response with invalid control character")
                return None
        
        # Exponential backoff
        time.sleep(delay)
        delay *= 2  # Double the delay each time
        retries += 1
        print(f"Retrying... attempt {retries}/{max_retries}")
    
    print("Max retries reached. Giving up.")
    return None

def save_results_to_file(results, filename="cpso_results.json"):
    """Save results to a JSON file"""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {filename}")

def run_simple_scrape(postal_codes, output_dir="data", doctor_type="Any", last_name="Any"):
    """
    Run a simple scrape with the provided postal codes
    
    Args:
        postal_codes: List of postal codes to search
        output_dir: Directory to save results
        doctor_type: Type of doctor to search for ("Any", "Family+Doctor", "Specialist")
        last_name: Last name to filter by ("Any" ignores this field)
    """
    results = fetch_results_with_rate_limit(
        postal_codes, 
        doctor_type=doctor_type,
        last_name=last_name,
        output_dir=output_dir
    )
    
    # Print summary
    total_doctors = sum(len(result.get('results', [])) for result in results)
    print(f"\nSummary: Retrieved information for {total_doctors} doctors across {len(postal_codes)} postal codes")
    return results

def load_postal_codes_from_file(input_file):
    """
    Load postal codes from a file
    
    Args:
        input_file: Path to the input file (JSON or CSV)
        
    Returns:
        List of postal codes
    """
    import pandas as pd
    
    try:
        if input_file.endswith('.json'):
            with open(input_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'postal_code' in data:
                    return [item['postal_code'] for item in data]
                else:
                    print(f"Unexpected JSON structure in {input_file}")
                    return []
        elif input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
            if 'postal_code' in df.columns:
                return df['postal_code'].tolist()
            else:
                # Use the first column if 'postal_code' doesn't exist
                return df.iloc[:, 0].tolist()
        else:
            # Treat as a simple text file with one code per line
            with open(input_file, 'r') as f:
                return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error loading postal codes from {input_file}: {e}")
        return []

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Scrape CPSO doctor registry using postal codes')
    parser.add_argument('--input-file', '-i', required=True,
                       help='Path to input file containing postal codes')
    parser.add_argument('--output-dir', '-o',
                       help='Directory to save results (defaults to input filename without extension)')
    parser.add_argument('--doctor-type', '-d', default="Any",
                       choices=["Any", "Family+Doctor", "Specialist"],
                       help='Type of doctor to search for (default: Any)')
    parser.add_argument('--last-name', '-l', default="Any",
                       help='Last name to filter by (default: Any)')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.")
        sys.exit(1)
    
    # Set output directory based on input filename if not specified
    if not args.output_dir:
        # Get the filename without extension
        input_path = Path(args.input_file)
        output_dir_name = input_path.stem  # Get filename without extension
        args.output_dir = os.path.join("data", output_dir_name)
    
    # Load postal codes from input file
    postal_codes = load_postal_codes_from_file(args.input_file)
    
    if not postal_codes:
        print("No postal codes loaded from input file. Exiting.")
        sys.exit(1)
    
    print(f"Loaded {len(postal_codes)} postal codes from {args.input_file}")
    print(f"Doctor type: {args.doctor_type}")
    print(f"Last name filter: {args.last_name}")
    print(f"Output will be saved to: {args.output_dir}")
    
    # Run the scrape
    run_simple_scrape(
        postal_codes, 
        args.output_dir,
        doctor_type=args.doctor_type,
        last_name=args.last_name
    )