# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This project scrapes doctor data from the College of Physicians and Surgeons of Ontario (CPSO) registry using postal codes.

## Commands
- Run scraper: `python code/scrape-cpso.py`
- Combine results: `python code/combine-scrapes.py`
- Validate data: `Rscript code/validation.R`

## Code Style Guidelines
- **Python**:
  - Use snake_case for functions and variables
  - Standard imports first, third-party libraries next
  - Use docstrings for functions
  - Implement rate limiting and exponential backoff for web scraping
  - Use pandas for data manipulation
  - Handle HTTP errors with appropriate retries and error messages
  - Use tqdm for progress indication in long-running tasks

- **R**:
  - Use tidyverse conventions with pipe operators (`|>`)
  - Load libraries at the top of scripts
  - Use the `here` package for file path management

## Data Organization
- Store raw scraping results in JSON files by postal code
- Use CSV files for consolidated and processed data
- Deduplicate records by CPSO number when combining data