"""
Web Scraper Module for E-Commerce Product Data
Fetches and extracts product details from books.toscrape.com using Requests and BeautifulSoup4.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import config

logger = logging.getLogger(__name__)


class ProductScraper:
    """
    Scraper designed to extract product details across multiple paginated pages
    with robust retry handling, politeness delays, and detailed logging.
    """

    def __init__(
        self,
        base_url: str = config.BASE_URL,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = config.REQUEST_TIMEOUT,
        delay: float = config.REQUEST_DELAY,
        max_retries: int = config.MAX_RETRIES,
        backoff_factor: float = config.BACKOFF_FACTOR,
    ):
        self.base_url = base_url
        self.headers = headers or config.DEFAULT_HEADERS
        self.timeout = timeout
        self.delay = delay
        self.session = self._create_session(max_retries, backoff_factor)

    def _create_session(self, max_retries: int, backoff_factor: float) -> requests.Session:
        """
        Configures and returns a requests.Session with exponential backoff retries
        for resilient network requests.
        """
        session = requests.Session()
        session.headers.update(self.headers)

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def fetch_page(self, url: str) -> Optional[str]:
        """
        Downloads the HTML text for a specific URL with error handling and timeouts.
        Returns HTML string on success, or None on failure.
        """
        try:
            logger.info("Fetching URL: %s", url)
            response = self.session.get(url, timeout=self.timeout)

            # Check HTTP status code
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                logger.warning("Page not found (404): %s", url)
                return None
            else:
                logger.warning(
                    "Unexpected HTTP status %s received for %s",
                    response.status_code,
                    url,
                )
                return None

        except requests.exceptions.Timeout:
            logger.error("Request timed out after %s seconds: %s", self.timeout, url)
            return None
        except requests.exceptions.ConnectionError as err:
            logger.error("Network connection error while fetching %s: %s", url, err)
            return None
        except requests.exceptions.RequestException as err:
            logger.error("Request failed for %s: %s", url, err)
            return None

    def parse_product(self, product_elem, current_page_url: str) -> Optional[Dict[str, Any]]:
        """
        Extracts product attributes from a single product card (<article class="product_pod">).
        Returns a dictionary of raw product values, or None if the card is malformed.
        """
        try:
            # 1. Product Name (Check 'title' attribute first to avoid truncation, fallback to text)
            title_tag = product_elem.select_one("h3 a")
            if not title_tag:
                logger.warning("Skipping product card: missing title anchor tag.")
                return None

            product_name = title_tag.get("title") or title_tag.get_text(strip=True)

            # 2. Product Price
            price_tag = product_elem.select_one("p.price_color")
            price_str = price_tag.get_text(strip=True) if price_tag else None

            # 3. Product Rating
            # The rating class is typically in the format: class="star-rating Three"
            rating_tag = product_elem.select_one("p.star-rating")
            rating_val = None
            if rating_tag and rating_tag.get("class"):
                # Filter out the generic 'star-rating' class to isolate the word rating
                rating_classes = [c for c in rating_tag.get("class") if c != "star-rating"]
                if rating_classes:
                    rating_val = rating_classes[0]

            # 4. Product Availability
            avail_tag = product_elem.select_one("p.availability, p.instock")
            availability_str = avail_tag.get_text(strip=True) if avail_tag else None

            # 5. Product Detail URL
            relative_url = title_tag.get("href", "")
            product_url = urljoin(current_page_url, relative_url) if relative_url else None

            # 6. Scraping Timestamp
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

            return {
                "product_name": product_name,
                "price": price_str,
                "rating": rating_val,
                "availability": availability_str,
                "product_url": product_url,
                "scraped_at": timestamp,
            }

        except Exception as err:
            logger.error("Error parsing product card: %s", err, exc_info=True)
            return None

    def extract_next_page(self, soup: BeautifulSoup, current_page_url: str) -> Optional[str]:
        """
        Locates the pagination 'next' button and resolves its absolute URL.
        Returns the absolute URL string, or None if on the final page.
        """
        next_tag = soup.select_one("li.next a")
        if next_tag and next_tag.get("href"):
            next_href = next_tag["href"]
            next_url = urljoin(current_page_url, next_href)
            return next_url
        return None

    def parse_page(self, html_content: str, current_page_url: str) -> List[Dict[str, Any]]:
        """
        Parses an HTML page, extracting all available product cards.
        """
        if not html_content or not html_content.strip():
            logger.warning("Empty or blank HTML content provided.")
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        product_elements = soup.select("article.product_pod")

        if not product_elements:
            logger.info("No product cards found on %s", current_page_url)
            return []

        products = []
        for elem in product_elements:
            item = self.parse_product(elem, current_page_url)
            if item:
                products.append(item)

        return products

    def scrape(
        self,
        start_url: Optional[str] = None,
        max_pages: Optional[int] = config.DEFAULT_MAX_PAGES,
    ) -> List[Dict[str, Any]]:
        """
        Executes the end-to-end multi-page scraping workflow.
        Handles pagination, politeness throttling, and gracefully stops at max_pages or end of data.
        """
        current_url = start_url or config.START_URL
        all_products: List[Dict[str, Any]] = []
        page_num = 1

        logger.info(
            "Starting scraping session. Target: %s | Max pages: %s",
            current_url,
            max_pages or "Unlimited",
        )

        while current_url:
            if max_pages is not None and page_num > max_pages:
                logger.info("Reached maximum requested pages limit (%s). Halting scrape.", max_pages)
                break

            logger.info("Scraping Page %d: %s", page_num, current_url)
            html = self.fetch_page(current_url)

            if not html:
                logger.warning("Failed to retrieve Page %d. Stopping pagination.", page_num)
                break

            soup = BeautifulSoup(html, "html.parser")
            page_products = self.parse_page(html, current_url)
            all_products.extend(page_products)

            logger.info(
                "Page %d parsed: %d products extracted (Total so far: %d)",
                page_num,
                len(page_products),
                len(all_products),
            )

            # Find next page
            current_url = self.extract_next_page(soup, current_url)
            page_num += 1

            # Respectful delay between page fetches
            if current_url and (max_pages is None or page_num <= max_pages):
                time.sleep(self.delay)

        logger.info("Scraping finished. Total items extracted: %d", len(all_products))
        return all_products
