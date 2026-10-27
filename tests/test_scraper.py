"""
Unit Tests for Scraper Module
Uses mock HTML snippets to test extraction, error handling, and pagination
without making real network calls.
"""

import unittest
from bs4 import BeautifulSoup
from scraper import ProductScraper


# Mock HTML representing http://books.toscrape.com/index.html (page 1)
ROOT_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Book Store</title></head>
<body>
<div class="page_inner">
    <section>
        <ol class="row">
            <li class="col-xs-6 col-sm-4 col-md-3 col-lg-3">
                <article class="product_pod">
                    <div class="image_container">
                        <a href="catalogue/a-light-in-the-attic_1000/index.html"><img src="media/cache/img1.jpg" alt="A Light in the Attic"/></a>
                    </div>
                    <p class="star-rating Three">
                        <i class="icon-star"></i>
                    </p>
                    <h3><a href="catalogue/a-light-in-the-attic_1000/index.html" title="A Light in the Attic">A Light in the ...</a></h3>
                    <div class="product_price">
                        <p class="price_color">£51.77</p>
                        <p class="instock availability"><i class="icon-ok"></i> In stock</p>
                    </div>
                </article>
            </li>
            <li class="col-xs-6 col-sm-4 col-md-3 col-lg-3">
                <article class="product_pod">
                    <div class="image_container">
                        <a href="catalogue/tipping-the-velvet_999/index.html"><img src="media/cache/img2.jpg" alt="Tipping the Velvet"/></a>
                    </div>
                    <p class="star-rating One">
                        <i class="icon-star"></i>
                    </p>
                    <h3><a href="catalogue/tipping-the-velvet_999/index.html" title="Tipping the Velvet">Tipping the Velvet</a></h3>
                    <div class="product_price">
                        <p class="price_color">£53.74</p>
                        <p class="instock availability"><i class="icon-ok"></i> In stock</p>
                    </div>
                </article>
            </li>
        </ol>
        <ul class="pager">
            <li class="next"><a href="catalogue/page-2.html">next</a></li>
        </ul>
    </section>
</div>
</body>
</html>
"""

# Mock HTML representing subsequent catalogue pages (e.g., catalogue/page-2.html)
CATALOGUE_PAGE_HTML = """
<!DOCTYPE html>
<html>
<body>
    <article class="product_pod">
        <p class="star-rating Four"></p>
        <h3><a href="in-her-wake_980/index.html" title="In Her Wake">In Her Wake</a></h3>
        <p class="price_color">£12.84</p>
        <p class="availability">In stock</p>
    </article>
    <ul class="pager">
        <li class="previous"><a href="page-1.html">previous</a></li>
        <li class="next"><a href="page-3.html">next</a></li>
    </ul>
</body>
</html>
"""

MALFORMED_PRODUCT_HTML = """
<article class="product_pod">
    <div>No title link here</div>
    <div class="product_price">
        <p class="price_color">£10.00</p>
    </div>
</article>
"""

LAST_PAGE_HTML = """
<html><body>
    <article class="product_pod">
        <h3><a href="final-book_1/index.html" title="Final Item">Final Item</a></h3>
        <p class="price_color">£9.99</p>
        <p class="star-rating Five"></p>
        <p class="availability">In stock</p>
    </article>
    <ul class="pager">
        <li class="previous"><a href="page-49.html">previous</a></li>
    </ul>
</body></html>
"""


class TestProductScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = ProductScraper()
        self.root_url = "http://books.toscrape.com/index.html"
        self.catalogue_url = "http://books.toscrape.com/catalogue/page-2.html"

    def test_parse_root_page_extracts_products(self):
        products = self.scraper.parse_page(ROOT_PAGE_HTML, self.root_url)
        self.assertEqual(len(products), 2)

    def test_parse_product_fields_and_attribute_resolution(self):
        products = self.scraper.parse_page(ROOT_PAGE_HTML, self.root_url)
        first = products[0]

        # Verify full title is extracted from title attribute rather than truncated link text
        self.assertEqual(first["product_name"], "A Light in the Attic")
        self.assertEqual(first["price"], "£51.77")
        self.assertEqual(first["rating"], "Three")
        self.assertEqual(first["availability"], "In stock")
        self.assertEqual(
            first["product_url"],
            "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        )
        self.assertIn("scraped_at", first)

    def test_pagination_from_root_page(self):
        soup = BeautifulSoup(ROOT_PAGE_HTML, "html.parser")
        next_url = self.scraper.extract_next_page(soup, self.root_url)
        self.assertEqual(next_url, "http://books.toscrape.com/catalogue/page-2.html")

    def test_pagination_and_urls_from_catalogue_page(self):
        soup = BeautifulSoup(CATALOGUE_PAGE_HTML, "html.parser")
        next_url = self.scraper.extract_next_page(soup, self.catalogue_url)
        self.assertEqual(next_url, "http://books.toscrape.com/catalogue/page-3.html")

        products = self.scraper.parse_page(CATALOGUE_PAGE_HTML, self.catalogue_url)
        self.assertEqual(len(products), 1)
        self.assertEqual(
            products[0]["product_url"],
            "http://books.toscrape.com/catalogue/in-her-wake_980/index.html",
        )
        self.assertEqual(products[0]["rating"], "Four")

    def test_pagination_last_page_returns_none(self):
        soup = BeautifulSoup(LAST_PAGE_HTML, "html.parser")
        next_url = self.scraper.extract_next_page(soup, "http://books.toscrape.com/catalogue/page-50.html")
        self.assertIsNone(next_url)

    def test_malformed_product_card_handled_gracefully(self):
        soup = BeautifulSoup(MALFORMED_PRODUCT_HTML, "html.parser")
        card = soup.find("article", class_="product_pod")
        result = self.scraper.parse_product(card, self.root_url)
        self.assertIsNone(result)

    def test_empty_html_returns_empty_list(self):
        products = self.scraper.parse_page("", self.root_url)
        self.assertEqual(products, [])

        products_whitespace = self.scraper.parse_page("   \n\t  ", self.root_url)
        self.assertEqual(products_whitespace, [])


if __name__ == "__main__":
    unittest.main()
