"""
Unit Tests for DataCleaner and DataAnalyzer Modules
Tests data sanitization, price parsing, rating conversion, deduplication,
summary calculations, and report generation.
"""

import unittest
import numpy as np
import pandas as pd

from data_cleaner import DataCleaner
from analyzer import DataAnalyzer


class TestDataCleaner(unittest.TestCase):
    def setUp(self):
        self.cleaner = DataCleaner()

    def test_extract_price_valid_and_variations(self):
        # Standard pound symbol
        self.assertEqual(self.cleaner.extract_price("£51.77"), 51.77)
        # Dollar symbol
        self.assertEqual(self.cleaner.extract_price("$19.99"), 19.99)
        # Encoding artifact Â£
        self.assertEqual(self.cleaner.extract_price("Â£10.50"), 10.50)
        # Genuine zero price
        self.assertEqual(self.cleaner.extract_price("£0.00"), 0.0)
        # Integer price
        self.assertEqual(self.cleaner.extract_price("45"), 45.0)

    def test_extract_price_missing_and_invalid(self):
        self.assertTrue(np.isnan(self.cleaner.extract_price(None)))
        self.assertTrue(np.isnan(self.cleaner.extract_price("")))
        self.assertTrue(np.isnan(self.cleaner.extract_price("N/A")))
        self.assertTrue(np.isnan(self.cleaner.extract_price("Out of Stock")))

    def test_convert_rating(self):
        self.assertEqual(self.cleaner.convert_rating("One"), 1)
        self.assertEqual(self.cleaner.convert_rating("two"), 2)
        self.assertEqual(self.cleaner.convert_rating("Three"), 3)
        self.assertEqual(self.cleaner.convert_rating("FOUR"), 4)
        self.assertEqual(self.cleaner.convert_rating("Five"), 5)
        self.assertEqual(self.cleaner.convert_rating("4"), 4)
        self.assertIsNone(self.cleaner.convert_rating("InvalidRating"))
        self.assertIsNone(self.cleaner.convert_rating(None))

    def test_clean_text(self):
        raw = "   A   Light in  \n the Attic   \t"
        self.assertEqual(self.cleaner.clean_text(raw), "A Light in the Attic")
        self.assertIsNone(self.cleaner.clean_text("   "))
        self.assertIsNone(self.cleaner.clean_text(None))

    def test_clean_deduplication_and_null_removal(self):
        raw_records = [
            {
                "product_name": "Book A",
                "price": "£10.00",
                "rating": "Three",
                "availability": "In stock",
                "product_url": "http://example.com/a",
                "scraped_at": "2026-10-27",
            },
            {
                # Exact duplicate of Book A
                "product_name": "Book A",
                "price": "£10.00",
                "rating": "Three",
                "availability": "In stock",
                "product_url": "http://example.com/a",
                "scraped_at": "2026-10-27",
            },
            {
                # Book with missing title should be dropped
                "product_name": None,
                "price": "£15.00",
                "rating": "Two",
                "availability": "In stock",
                "product_url": "http://example.com/none",
                "scraped_at": "2026-10-27",
            },
            {
                "product_name": "Book B",
                "price": "£25.50",
                "rating": "Five",
                "availability": "In stock",
                "product_url": "http://example.com/b",
                "scraped_at": "2026-10-27",
            },
        ]

        df = self.cleaner.clean(raw_records)
        self.assertEqual(len(df), 2)
        self.assertListEqual(list(df["product_name"]), ["Book A", "Book B"])
        self.assertEqual(df.loc[df["product_name"] == "Book A", "price"].values[0], 10.0)
        self.assertEqual(df.loc[df["product_name"] == "Book A", "rating"].values[0], 3)

    def test_clean_empty_records(self):
        df = self.cleaner.clean([])
        self.assertTrue(df.empty)
        self.assertListEqual(list(df.columns), self.cleaner.EXPECTED_COLUMNS)


class TestDataAnalyzer(unittest.TestCase):
    def setUp(self):
        self.sample_df = pd.DataFrame([
            {"product_name": "Book 1", "price": 10.0, "rating": 1, "availability": "In stock"},
            {"product_name": "Book 2", "price": 20.0, "rating": 3, "availability": "In stock"},
            {"product_name": "Book 3", "price": 30.0, "rating": 5, "availability": "In stock"},
            {"product_name": "Book 4", "price": np.nan, "rating": pd.NA, "availability": "Out of stock"},
        ])
        self.analyzer = DataAnalyzer(self.sample_df)

    def test_compute_summary_metrics(self):
        summary = self.analyzer.compute_summary()
        self.assertEqual(summary["total_products"], 4)
        self.assertEqual(summary["unique_products"], 4)
        self.assertEqual(summary["price_count"], 3)
        self.assertEqual(summary["avg_price"], 20.0)
        self.assertEqual(summary["min_price"], 10.0)
        self.assertEqual(summary["max_price"], 30.0)
        self.assertEqual(summary["median_price"], 20.0)
        self.assertEqual(summary["availability_counts"]["In stock"], 3)
        self.assertEqual(summary["availability_counts"]["Out of stock"], 1)

    def test_compute_summary_empty_dataframe(self):
        empty_analyzer = DataAnalyzer(pd.DataFrame(columns=["product_name", "price", "rating", "availability"]))
        summary = empty_analyzer.compute_summary()
        self.assertEqual(summary["total_products"], 0)
        self.assertEqual(summary["avg_price"], 0.0)


if __name__ == "__main__":
    unittest.main()
