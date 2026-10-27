"""
Configuration Module for E-Commerce Product Data Scraper
Contains constants, file paths, HTTP headers, and scraping parameters.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Data Export Paths
RAW_DATA_PATH = DATA_DIR / "raw_products.csv"
CLEANED_DATA_PATH = DATA_DIR / "cleaned_products.csv"
EXCEL_DATA_PATH = DATA_DIR / "products.xlsx"

# Analysis and Visualization Output Paths
SUMMARY_REPORT_PATH = OUTPUT_DIR / "summary_report.txt"
PRICE_DIST_CHART_PATH = OUTPUT_DIR / "price_distribution.png"
RATING_DIST_CHART_PATH = OUTPUT_DIR / "rating_distribution.png"
PRICE_BY_RATING_CHART_PATH = OUTPUT_DIR / "price_by_rating.png"

# Logging Path
LOG_FILE_PATH = LOGS_DIR / "scraper.log"

# Target Website Settings (books.toscrape.com - authorized sandbox)
BASE_URL = "http://books.toscrape.com/"
START_URL = "http://books.toscrape.com/index.html"

# HTTP & Scraping Settings
DEFAULT_MAX_PAGES = 5  # Set to None to scrape all pages (e.g., 50 pages on books.toscrape)
REQUEST_TIMEOUT = 15   # seconds
REQUEST_DELAY = 1.0    # seconds delay between page requests for politeness
MAX_RETRIES = 3        # retry attempts on transient network failures
BACKOFF_FACTOR = 0.5   # exponential backoff factor

# Descriptive and respectful User-Agent
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 "
    "(EducationalScraper/1.0; +https://github.com/example/product-data-scraper)"
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

# Star rating conversion mapping
RATING_MAP = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}
