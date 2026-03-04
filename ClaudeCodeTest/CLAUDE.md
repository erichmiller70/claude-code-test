# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python web scraping project. The main script (`scrapetest.py`) scrapes country data from scrapethissite.com and writes it to `countries.csv`.

## Dependencies

- Python 3
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing

Install: `pip install requests beautifulsoup4`

## Running

```bash
python scrapetest.py
```

Output: `countries.csv` with columns Name, Capital, Population, Area.
