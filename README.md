# E-Commerce Product Data Scraper & Price Analysis System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![BeautifulSoup4](https://img.shields.io/badge/BeautifulSoup4-4.12%2B-green.svg)](https://beautiful-soup-4.readthedocs.io/)
[![Requests](https://img.shields.io/badge/Requests-2.31%2B-orange.svg)](https://requests.readthedocs.io/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-darkblue.svg)](https://pandas.pydata.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An end-to-end, production-grade Python web scraping and exploratory data analysis pipeline. It extracts catalog data across multiple paginated pages from [books.toscrape.com](http://books.toscrape.com/) (an authorized scraping sandbox), cleans and validates the extracted records with **Pandas**, exports structured datasets to **CSV** and styled **Excel** spreadsheets via **OpenPyXL**, and generates descriptive statistics and high-resolution visual charts using **Matplotlib**.

---

## Architecture & System Flow

```
+-----------------------------------------------------------------------+
|                           Target Website                              |
|                      (books.toscrape.com)                             |
+-----------------------------------------------------------------------+
                                   |
                                   | HTTP GET (User-Agent, Retries, Backoff)
                                   v
+-----------------------------------------------------------------------+
|                    1. Scraper Module (scraper.py)                     |
|  - Manages persistent HTTP sessions via Requests                      |
|  - Extracts product pods via BeautifulSoup4 CSS selectors             |
|  - Resolves relative URLs (urljoin) for products & pagination         |
|  - Throttles requests with politeness delays                          |
+-----------------------------------------------------------------------+
                                   |
                                   | Raw Records (List of Dicts)
                                   v
+-----------------------------------------------------------------------+
|                  2. Data Cleaner (data_cleaner.py)                    |
|  - Saves raw baseline dataset (data/raw_products.csv)                 |
|  - Deduplicates records by product_name & product_url                 |
|  - Standardizes text & cleans whitespace/newlines                     |
|  - Converts price strings to numeric floats (£51.77 -> 51.77)         |
|  - Preserves distinction between missing (NaN) and £0.00              |
|  - Converts star rating words ('Three' -> 3)                          |
|  - Exports sanitized CSV (data/cleaned_products.csv)                  |
|  - Generates styled Excel file with OpenPyXL (data/products.xlsx)     |
+-----------------------------------------------------------------------+
                                   |
                                   | Cleaned DataFrame
                                   v
+-----------------------------------------------------------------------+
|                    3. Analyzer (analyzer.py)                          |
|  - Computes descriptive metrics (mean, median, min, max, std dev)     |
|  - Breaks down rating distributions and stock availability            |
|  - Saves formatted report (output/summary_report.txt)                 |
|  - Renders 300 DPI Matplotlib charts:                                 |
|      * output/price_distribution.png                                  |
|      * output/rating_distribution.png                                 |
|      * output/price_by_rating.png                                     |
+-----------------------------------------------------------------------+
```

---

## Directory Structure

```
product-data-scraper/
|-- config.py                 # Central configuration (URLs, headers, timeouts, file paths)
|-- scraper.py                # Web scraper engine (Session, retries, parsing, pagination)
|-- data_cleaner.py           # Pandas cleaning, schema validation, CSV/Excel export
|-- analyzer.py               # Statistical computations and Matplotlib chart generation
|-- main.py                   # Orchestration CLI entry point
|-- requirements.txt          # Python project dependencies
|-- .gitignore                # Git ignore rules for virtualenvs, caches, logs, outputs
|-- README.md                 # Complete project documentation
|-- data/                     # Output datasets
|   |-- raw_products.csv      # Unprocessed scraped records
|   |-- cleaned_products.csv  # Sanitized, deduplicated tabular data
|   `-- products.xlsx         # Formatted Excel workbook with styled headers
|-- output/                   # Analysis reports and visualization figures
|   |-- summary_report.txt    # Printable statistical summary
|   |-- price_distribution.png# Price histogram with mean & median indicators
|   |-- rating_distribution.png# Rating frequency bar chart
|   `-- price_by_rating.png   # Average price per star rating bar chart
|-- logs/                     # Application execution logs
|   `-- scraper.log           # Timestamped log records (DEBUG and INFO)
`-- tests/                    # Unit tests using offline mock HTML
    |-- test_scraper.py       # Scraper extraction & pagination tests
    `-- test_cleaner.py       # Data cleaning & statistical calculation tests
```

---

## Technology Stack

| Technology | Purpose |
| :--- | :--- |
| **Python 3.10+** | Core programming language |
| **Requests** | HTTP client with connection pooling, timeouts, and headers |
| **Urllib3** | Resilient retry strategies with exponential backoff |
| **BeautifulSoup4** | HTML parsing and DOM navigation via CSS selectors |
| **Pandas** | Tabular data manipulation, deduplication, and type coercion |
| **OpenPyXL** | Creation and styling of native Excel `.xlsx` workbooks |
| **Matplotlib** | Headless rendering of statistical charts and distributions |
| **Unittest** | Automated offline testing with mock HTML fixtures |

---

## Step-by-Step Windows Setup Guide

### 1. Open Windows Command Prompt (CMD)
Press `Win + R`, type `cmd`, and press `Enter`.

### 2. Navigate to your desired workspace
```cmd
cd C:\Users\Aniket\.gemini\antigravity\scratch\product-data-scraper
```

### 3. Create a Virtual Environment
Creating an isolated virtual environment (`.venv`) ensures that project dependencies do not interfere with system-wide packages:
```cmd
python -m venv .venv
```

### 4. Activate the Virtual Environment
- **On Windows CMD:**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **On Windows PowerShell (if preferred):**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
*(When activated, you will see `(.venv)` at the beginning of your command prompt.)*

### 5. Upgrade pip and Install Dependencies
```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## How to Run the Application

### Basic Run (Scrapes 5 pages by default)
```cmd
python main.py
```

### Custom Page Limit
Scrape only 2 pages for quick testing:
```cmd
python main.py --max-pages 2
```

### Scrape the Entire Catalog
To scrape all available pages on the site until pagination terminates naturally:
```cmd
python main.py --max-pages 0
```

### Enable Debug Logs and Adjust Politeness Delay
```cmd
python main.py --max-pages 3 --delay 1.5 --verbose
```

---

## Detailed Explanation of Files & Core Functions

### 1. `config.py`
Acts as the single source of truth for the entire application:
- `BASE_URL` & `START_URL`: Starting endpoints for the target website.
- `DEFAULT_HEADERS`: Defines a descriptive `User-Agent` identifying the bot respectfully to web servers.
- `REQUEST_TIMEOUT` (15s) & `REQUEST_DELAY` (1.0s): Protects against hanging connections and prevents server overload.
- `RATING_MAP`: Dictionary mapping rating words (`"One"`, `"Two"`, `"Three"`, etc.) to numeric integers (`1`, `2`, `3`, etc.).
- `DATA_DIR`, `OUTPUT_DIR`, `LOGS_DIR`: Predefined directory paths using `pathlib.Path` that are automatically created at launch.

### 2. `scraper.py`
Handles all networking and HTML parsing logic:
- **`ProductScraper._create_session()`**: Builds a `requests.Session` equipped with `urllib3.util.Retry`. If the server returns temporary codes like `429` (Rate Limited), `500`, `502`, `503`, or `504`, it automatically waits and retries with exponential backoff instead of failing immediately.
- **`ProductScraper.fetch_page(url)`**: Safely sends HTTP GET requests with custom headers and timeouts. Validates the status code (`200 OK`) and logs detailed warnings if a page is missing (`404`) or drops connection.
- **`ProductScraper.parse_product(product_elem, current_page_url)`**: Inspects a single `<article class="product_pod">` element:
  - Extracts the full title from the `title` attribute of the `<h3><a title="...">` tag, preventing link-text truncation (e.g. `"A Light in the ..."` becomes `"A Light in the Attic"`).
  - Extracts the raw price text from `<p class="price_color">`.
  - Determines star ratings by reading the CSS classes on `<p class="star-rating Three">`.
  - Extracts the stock status from `<p class="availability">`.
  - Converts relative product links (e.g., `catalogue/book_1/index.html`) into absolute URLs using `urllib.parse.urljoin`.
  - Attaches an ISO/UTC scraping timestamp.
- **`ProductScraper.extract_next_page(soup, current_page_url)`**: Locates `<li class="next"><a href="...">` and builds the next page's absolute URL. Returns `None` when the last page is reached.
- **`ProductScraper.scrape(start_url, max_pages)`**: Orchestrates pagination loop, invokes politeness throttling via `time.sleep()`, and aggregates all scraped records into a list of dictionaries.

### 3. `data_cleaner.py`
Standardizes and validates raw scraped data:
- **`DataCleaner.export_raw(records)`**: Saves the unprocessed records directly to `data/raw_products.csv` as an audit trail.
- **`DataCleaner.extract_price(val)`**: Uses regular expressions (`r'(\d+(?:\.\d+)?)'`) to strip currency symbols (`£`, `$`, `€`, encoding artifacts like `Â£`) and converts numbers into `float`. Critically keeps a distinction between a true zero price (`0.0`) and missing values (`np.nan`).
- **`DataCleaner.convert_rating(val)`**: Maps text ratings (`'One'`, `'Two'`, `'Three'`) to nullable integers (`1`, `2`, `3`) using Pandas' `Int64` type.
- **`DataCleaner.clean_text(val)`**: Strips leading/trailing whitespace and collapses repeated internal whitespace or newlines into single spaces.
- **`DataCleaner.clean(records)`**: Removes duplicate entries based on `(product_name, product_url)` and drops records where required titles are missing.
- **`DataCleaner.export_cleaned(df)`**: Writes the sanitized DataFrame to `data/cleaned_products.csv` and builds an Excel workbook (`data/products.xlsx`) with custom dark-blue headers and auto-fitted column widths using `openpyxl`.

### 4. `analyzer.py`
Transforms the clean dataset into statistical insights and charts:
- **`DataAnalyzer.compute_summary()`**: Calculates total products, unique products, mean price, median price, minimum and maximum price, standard deviation, rating counts, and stock availability breakdown.
- **`DataAnalyzer.generate_text_report(summary)`**: Formats metrics into a readable text table and saves it to `output/summary_report.txt`.
- **`DataAnalyzer.plot_price_distribution()`**: Uses Matplotlib to plot a price frequency histogram with highlighted mean and median vertical reference lines.
- **`DataAnalyzer.plot_rating_distribution()`**: Plots a bar chart displaying the frequency of each star rating (1 to 5 stars) with count labels directly above each bar.
- **`DataAnalyzer.plot_price_by_rating()`**: Plots average product price grouped by star rating.

### 5. `main.py`
The master entry point:
- Sets up unified dual logging (console + `logs/scraper.log`).
- Parses CLI parameters (`--max-pages`, `--delay`, `--start-url`, `--verbose`).
- Executes the pipeline sequentially: **Scrape -> Raw Export -> Clean -> Clean Export -> Analyze -> Visualize**.

---

## Sample Output

### 1. Terminal Summary Report (`output/summary_report.txt`)
```
=================================================================
       E-COMMERCE PRODUCT DATA SCRAPER & PRICE ANALYSIS       
=================================================================
 Total Products Scraped : 60
 Unique Product Titles  : 60
-----------------------------------------------------------------
 PRICE METRICS (GBP):
   Valid Price Entries  : 60
   Average (Mean) Price : GBP 35.00
   Median Price         : GBP 33.48
   Minimum Price        : GBP 12.84
   Maximum Price        : GBP 57.31
   Standard Deviation   : GBP 14.55
-----------------------------------------------------------------
 PRODUCT RATINGS BREAKDOWN:
   * 1 Stars             :   15 items ( 25.0%)
   * 2 Stars             :    8 items ( 13.3%)
   * 3 Stars             :   13 items ( 21.7%)
   * 4 Stars             :   10 items ( 16.7%)
   * 5 Stars             :   14 items ( 23.3%)
-----------------------------------------------------------------
 AVAILABILITY BREAKDOWN:
   * In stock            :   60 items (100.0%)
=================================================================
```

### 2. Sample Data Rows (`data/cleaned_products.csv`)
| product_name | price | rating | availability | product_url | scraped_at |
| :--- | :--- | :--- | :--- | :--- | :--- |
| A Light in the Attic | 51.77 | 3 | In stock | `http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html` | 2026-10-27 12:40:31 UTC |
| Tipping the Velvet | 53.74 | 1 | In stock | `http://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html` | 2026-10-27 12:40:31 UTC |
| Soumission | 50.10 | 1 | In stock | `http://books.toscrape.com/catalogue/soumission_998/index.html` | 2026-10-27 12:40:31 UTC |
| Sharp Objects | 47.82 | 4 | In stock | `http://books.toscrape.com/catalogue/sharp-objects_997/index.html` | 2026-10-27 12:40:31 UTC |
| Sapiens: A Brief History of Humankind | 54.23 | 5 | In stock | `http://books.toscrape.com/catalogue/sapiens-a-brief-history-of-humankind_996/index.html` | 2026-10-27 12:40:31 UTC |

---

## Running the Unit Tests

The test suite runs entirely offline using realistic mock HTML strings. It tests HTML parsing, pagination resolution, edge cases, malformed HTML, price conversions, and deduplication:

```cmd
python -m unittest discover -s tests -p "test_*.py" -v
```

Expected output:
```
test_compute_summary_empty_dataframe (test_cleaner.TestDataAnalyzer) ... ok
test_compute_summary_metrics (test_cleaner.TestDataAnalyzer) ... ok
test_clean_deduplication_and_null_removal (test_cleaner.TestDataCleaner) ... ok
test_clean_empty_records (test_cleaner.TestDataCleaner) ... ok
test_clean_text (test_cleaner.TestDataCleaner) ... ok
test_convert_rating (test_cleaner.TestDataCleaner) ... ok
test_extract_price_missing_and_invalid (test_cleaner.TestDataCleaner) ... ok
test_extract_price_valid_and_variations (test_cleaner.TestDataCleaner) ... ok
test_empty_html_returns_empty_list (test_scraper.TestProductScraper) ... ok
test_malformed_product_card_handled_gracefully (test_scraper.TestProductScraper) ... ok
test_pagination_and_urls_from_catalogue_page (test_scraper.TestProductScraper) ... ok
test_pagination_from_root_page (test_scraper.TestProductScraper) ... ok
test_pagination_last_page_returns_none (test_scraper.TestProductScraper) ... ok
test_parse_product_fields_and_attribute_resolution (test_scraper.TestProductScraper) ... ok
test_parse_root_page_extracts_products (test_scraper.TestProductScraper) ... ok

----------------------------------------------------------------------
Ran 15 tests in 0.088s

OK
```

---

## Adapting the Scraper for Other Websites

To point this scraper to a different e-commerce site, follow this systematic workflow:

### Step 1: Check Permissions & Robots.txt
Always check `https://example.com/robots.txt` before scraping. Ensure automated access is permitted for your target paths, and honor all crawl delays and exclusions.

### Step 2: Inspect the Page with Chrome DevTools
1. Open Chrome or Firefox, go to the target website, right-click on a product card, and select **Inspect**.
2. Find the repeating parent container tag (e.g. `<div class="product-item">` or `<li class="card">`).
3. Update `soup.select(...)` in `scraper.py` to match the container.

### Step 3: Identify CSS Selectors for Each Field
- **Title / Name**: Inspect the title element. Check if the full text is in an attribute like `title` or within the inner text:
  ```python
  title_tag = product_elem.select_one(".product-title a")
  name = title_tag.get_text(strip=True)
  ```
- **Price**: Inspect the price element:
  ```python
  price_tag = product_elem.select_one("span.current-price")
  ```
- **Next Page Button**: Inspect the pagination navigation bar:
  ```python
  next_tag = soup.select_one("a.pagination__next, a[rel='next']")
  ```

### Step 4: Update `config.py`
Change `BASE_URL` and `START_URL` to the new website.

---

## Common Errors & Step-by-Step Solutions

| Error | Root Cause | Solution |
| :--- | :--- | :--- |
| `HTTP 403 Forbidden` | Server blocks default Python Requests User-Agent. | Set a realistic browser User-Agent in `config.py` (already configured in `DEFAULT_HEADERS`). |
| `AttributeError: 'NoneType' object has no attribute 'get_text'` | A CSS selector did not find a matching element on the page. | Use `.select_one(...)` with defensive `if tag:` checks, as demonstrated in `scraper.parse_product()`. |
| `ConnectionError: Max retries exceeded` | Target website server is unreachable or internet connection is down. | Verify your internet connection. The `ProductScraper` class includes automatic exponential backoff retries. |
| `ModuleNotFoundError: No module named '...'` | Virtual environment is not activated or dependencies are uninstalled. | Run `.venv\Scripts\activate.bat` and run `pip install -r requirements.txt`. |
| `PermissionError: [Errno 13] Permission denied: '...products.xlsx'` | The Excel file is open in Microsoft Excel while the script tries to overwrite it. | Close `products.xlsx` in Excel and run the script again. |
| Encoding Artifacts (e.g., `Â£`) | Mismatched UTF-8 decoding of European currency symbols on Windows CMD. | Cleaned automatically by `DataCleaner.extract_price()`, which isolates pure numeric float values. |


---

## License

This project is licensed under the MIT License - feel free to use it for educational and portfolio purposes.
