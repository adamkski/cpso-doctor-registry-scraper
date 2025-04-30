# CPSO Doctor Registry Scraper

A tool for scraping doctor information from the College of Physicians and Surgeons of Ontario (CPSO) registry using postal codes.

## Quick Start Tutorial

This project follows an iterative workflow to find all doctors in the CPSO registry:

1. **Get initial postal codes:**
   ```bash
   python code/scrape-postal-codes.py
   ```
   This creates postal code data to start the search.

2. **Scrape the CPSO registry:**
   ```bash
   python code/scrape-cpso.py --input-file data/search-criteria/FSA-LDU0.json
   ```
   The data will automatically be saved in subfolders of `data`.

3. **Create summarized outputs:**
   ```bash
   python code/create-output.py --input "data/initial_postal_codes/raw/*.json"
   ```
   Generates `results/summary.csv` and `results/details.csv`.

4. **Generate more specific postal codes for searches that hit the 100 results limit:**
   ```bash
   python code/create-postal-code-permutations.py 1 --input_file results/summary.csv
   ```
   This breaks down searches that returned too many results (totalcount = -1) into more specific postal codes.

5. **Repeat steps 2-4 with each level of permutations until satisfied:**
   ```bash
   # Scrape with the first level of permutations (LDU1)
   python code/scrape-cpso.py --input-file data/search-criteria/FSA_LDU1.json
   
   # Create outputs from the new scrape
   python code/create-output.py --input "data/FSA_LDU1/raw/*.json"
   
   # Generate next level permutations (if needed)
   python code/create-postal-code-permutations.py 2 --input_file results/summary.csv
   ```

## Advanced Usage

### Search filters

You can specify the doctor type when scraping:
```bash
python code/scrape-cpso.py --input-file data/search-criteria/FSA_LDU1.json --doctor-type "Family+Doctor"
```

Available doctor types:
- `Any` (default)
- `Family+Doctor`
- `Specialist`

You can also filter by last name:
```bash
python code/scrape-cpso.py --input-file data/search-criteria/FSA_LDU1.json --last-name "Smith"
```

### Custom output location
```bash
python code/scrape-cpso.py --input-file data/search-criteria/FSA_LDU1.json --output-dir data/custom_output
```

## Permutation Levels

The scraper works with these permutation levels:
1. Level 1 (LDU1): 4-character postal codes (e.g., K1A+2)
2. Level 2 (LDU2): 5-character postal codes (e.g., K1A+2A)
3. Level 3 (LDU3): 6-character postal codes (full postal code, e.g., K1A+2A3)

## Project Structure

- `code/` - Contains all scripts
- `data/` - Raw scrape results
- `results/` - Processed CSV outputs 

## Data Outputs

- `summary.csv` - Contains postal codes and their total result counts
- `details.csv` - Contains doctor details, deduplicated by CPSO number

## Important Notes

- The scraper implements rate limiting and exponential backoff to avoid overloading the CPSO server
- Use responsibly and respect CPSO's terms of service

## Requirements

- Python 3.x
- Required Python packages:
  - pandas
  - requests
  - tqdm