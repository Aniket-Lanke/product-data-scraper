"""
Main Application Entry Point for E-Commerce Product Data Scraper
Orchestrates scraping, cleaning, export, statistical analysis, and visualization.
"""

import argparse
import logging
import sys
from pathlib import Path

import config
from analyzer import DataAnalyzer
from data_cleaner import DataCleaner
from scraper import ProductScraper


def setup_logging(log_file: Path = config.LOG_FILE_PATH, verbose: bool = False) -> None:
    """
    Configures simultaneous logging to console and a persistent log file.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if verbose else logging.INFO

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)-7s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    # Clear existing handlers if re-run
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def parse_arguments() -> argparse.Namespace:
    """
    Parses user command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="E-Commerce Product Data Scraper and Price Analysis System"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=config.DEFAULT_MAX_PAGES,
        help=f"Maximum pages to scrape (default: {config.DEFAULT_MAX_PAGES}). Set 0 or negative for all pages.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=config.REQUEST_DELAY,
        help=f"Politeness delay between page requests in seconds (default: {config.REQUEST_DELAY}).",
    )
    parser.add_argument(
        "--start-url",
        type=str,
        default=config.START_URL,
        help=f"Starting URL for the scraper (default: {config.START_URL}).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed DEBUG level logs in console output.",
    )
    return parser.parse_args()


def main() -> int:
    """
    Main orchestration routine.
    """
    args = parse_arguments()
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger("main")

    print("\n" + "=" * 65)
    print("   E-COMMERCE PRODUCT DATA SCRAPER & PRICE ANALYSIS SYSTEM   ")
    print("=" * 65 + "\n")

    max_pages = None if args.max_pages <= 0 else args.max_pages

    logger.info("Initializing Product Scraper...")
    scraper = ProductScraper(delay=args.delay)

    # 1. Scraping Step
    try:
        raw_products = scraper.scrape(start_url=args.start_url, max_pages=max_pages)
    except KeyboardInterrupt:
        logger.warning("Scraping interrupted by user. Proceeding with collected data...")
        raw_products = []
    except Exception as err:
        logger.error("Fatal error during scraping: %s", err, exc_info=True)
        return 1

    if not raw_products:
        logger.error("No product records were retrieved. Please check network connection or URL.")
        return 1

    logger.info("Successfully scraped %d raw product entries.", len(raw_products))

    # 2. Data Cleaning & Export Step
    logger.info("Initializing Data Cleaner...")
    cleaner = DataCleaner()

    # Export raw data
    cleaner.export_raw(raw_products, filepath=config.RAW_DATA_PATH)

    # Clean records
    df_cleaned = cleaner.clean(raw_products)

    if df_cleaned.empty:
        logger.error("All scraped records were filtered out during validation. Aborting.")
        return 1

    # Export cleaned data (CSV and Excel)
    cleaner.export_cleaned(
        df_cleaned,
        csv_path=config.CLEANED_DATA_PATH,
        excel_path=config.EXCEL_DATA_PATH,
    )

    # 3. Analysis & Visualization Step
    logger.info("Running Statistical Analysis and Visualizations...")
    analyzer = DataAnalyzer(df_cleaned)

    # Compute stats & print text report
    summary_stats = analyzer.compute_summary()
    report_text = analyzer.generate_text_report(summary_stats, output_path=config.SUMMARY_REPORT_PATH)
    print("\n" + report_text + "\n")

    # Generate charts
    chart_paths = analyzer.run_all_visualizations()

    # 4. Completion Summary
    print("\n" + "=" * 65)
    print("                        PIPELINE COMPLETE                     ")
    print("=" * 65)
    print(f" [+] Raw CSV Data      : {config.RAW_DATA_PATH}")
    print(f" [+] Cleaned CSV Data  : {config.CLEANED_DATA_PATH}")
    print(f" [+] Excel Workbook    : {config.EXCEL_DATA_PATH}")
    print(f" [+] Text Report       : {config.SUMMARY_REPORT_PATH}")
    for name, path in chart_paths.items():
        if path:
            print(f" [+] Chart ({name:<12}): {path}")
    print(f" [+] Execution Log     : {config.LOG_FILE_PATH}")
    print("=" * 65 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
