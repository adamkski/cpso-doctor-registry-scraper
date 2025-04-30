# Use wikipedia to generate lists of FSAs
import json
import time
import random
import re
import requests
from bs4 import BeautifulSoup
import itertools
import string
import pandas as pd

def fetch_forward_sortation_areas_with_delay(urls, delay_range=(2, 5)):

    all_results = []

    for url in urls:
        # Random delay between requests
        delay = random.uniform(delay_range[0], delay_range[1])
        time.sleep(delay)

        print(f"Fetching FSAs for url {url}...")
        
        result_data = fetch_FSA(url)

        if result_data:
            all_results.append(result_data)
            print(f"Retrieved {len(result_data)} results for {url}")

    return all_results 

def fetch_FSA(url):

    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    b_tags = soup.find_all("b")

    # keep only strings that look like a FSA i.e. letter number letter
    pattern = re.compile("[A-Z][0-9][A-Z]")
    b_tags_filtered = [tag.get_text() for tag in b_tags if pattern.match(tag.get_text())]

    return b_tags_filtered

def save_results_to_file(results, filename="data/search-criteria/FSA_LDU0.json"):
    """Save results to a JSON file"""
    import json
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {filename}")


if __name__ == "__main__":
    urls = ["https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_K",        
        "https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_L",
        "https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M",
        "https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_N",
        "https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_P"]

    all_fsas = fetch_forward_sortation_areas_with_delay(urls)
    all_fsas_flat = [item for sublist in all_fsas for item in sublist]

    # Save results to file
    save_results_to_file(all_fsas_flat)
    
    # Print summary
    total_fsas = sum(len(result) for result in all_fsas)
    print(f"\nSummary: Retrieved {total_fsas} FSAs across {len(urls)} Wikipedia pages")