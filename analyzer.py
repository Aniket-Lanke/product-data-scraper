"""
Data Analysis and Visualization Module
Calculates descriptive statistics, generates summary reports,
and creates publication-ready visual charts using Matplotlib.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure Matplotlib uses a headless backend and a writable config directory
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import config

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """
    Performs exploratory data analysis on cleaned product records,
    prints summary metrics, and generates visual charts.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def compute_summary(self) -> Dict[str, Any]:
        """
        Calculates key statistical aggregates for prices, ratings, and availability.
        """
        if self.df.empty:
            logger.warning("Empty DataFrame passed to compute_summary.")
            return {
                "total_products": 0,
                "unique_products": 0,
                "price_count": 0,
                "avg_price": 0.0,
                "median_price": 0.0,
                "min_price": 0.0,
                "max_price": 0.0,
                "std_price": 0.0,
                "rating_counts": {},
                "availability_counts": {},
            }

        price_series = self.df["price"].dropna()

        summary = {
            "total_products": int(len(self.df)),
            "unique_products": int(self.df["product_name"].nunique()),
            "price_count": int(price_series.count()),
            "avg_price": round(float(price_series.mean()), 2) if not price_series.empty else 0.0,
            "median_price": round(float(price_series.median()), 2) if not price_series.empty else 0.0,
            "min_price": round(float(price_series.min()), 2) if not price_series.empty else 0.0,
            "max_price": round(float(price_series.max()), 2) if not price_series.empty else 0.0,
            "std_price": round(float(price_series.std()), 2) if len(price_series) > 1 else 0.0,
            "rating_counts": self.df["rating"].value_counts(dropna=False).sort_index().to_dict(),
            "availability_counts": self.df["availability"].value_counts(dropna=False).to_dict(),
        }
        return summary

    def generate_text_report(
        self,
        summary: Optional[Dict[str, Any]] = None,
        output_path: Path = config.SUMMARY_REPORT_PATH,
    ) -> str:
        """
        Formats a clean text summary report, writes it to disk, and returns the formatted text.
        """
        stats = summary or self.compute_summary()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "=" * 65,
            "       E-COMMERCE PRODUCT DATA SCRAPER & PRICE ANALYSIS       ",
            "=" * 65,
            f" Total Products Scraped : {stats['total_products']}",
            f" Unique Product Titles  : {stats['unique_products']}",
            "-" * 65,
            " PRICE METRICS (GBP):",
            f"   Valid Price Entries  : {stats['price_count']}",
            f"   Average (Mean) Price : GBP {stats['avg_price']:.2f}",
            f"   Median Price         : GBP {stats['median_price']:.2f}",
            f"   Minimum Price        : GBP {stats['min_price']:.2f}",
            f"   Maximum Price        : GBP {stats['max_price']:.2f}",
            f"   Standard Deviation   : GBP {stats['std_price']:.2f}",
            "-" * 65,
            " PRODUCT RATINGS BREAKDOWN:",
        ]

        # Ratings formatting
        for stars, count in sorted(stats["rating_counts"].items(), key=lambda x: (str(x[0]))):
            label = f"{stars} Stars" if pd.notna(stars) else "Unrated / Missing"
            pct = (count / stats["total_products"] * 100) if stats["total_products"] else 0
            lines.append(f"   * {label:<20}: {count:>4} items ({pct:>5.1f}%)")

        lines.append("-" * 65)
        lines.append(" AVAILABILITY BREAKDOWN:")
        for status, count in stats["availability_counts"].items():
            label = str(status) if pd.notna(status) else "Unknown"
            pct = (count / stats["total_products"] * 100) if stats["total_products"] else 0
            lines.append(f"   * {label:<20}: {count:>4} items ({pct:>5.1f}%)")

        lines.append("=" * 65)
        report_text = "\n".join(lines)

        output_path.write_text(report_text, encoding="utf-8")
        logger.info("Summary report written to: %s", output_path)
        return report_text

    def plot_price_distribution(self, output_path: Path = config.PRICE_DIST_CHART_PATH) -> Optional[Path]:
        """
        Generates and saves a histogram showing product price distribution.
        """
        prices = self.df["price"].dropna()
        if prices.empty:
            logger.warning("No price data available to plot price distribution.")
            return None

        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.figure(figsize=(9, 5.5))
        
        # Plot histogram
        n, bins, patches = plt.hist(
            prices,
            bins=15,
            color="#2b5c8f",
            edgecolor="#142c44",
            alpha=0.85,
        )

        mean_val = prices.mean()
        median_val = prices.median()

        plt.axvline(
            mean_val,
            color="#d9534f",
            linestyle="--",
            linewidth=2,
            label=f"Mean Price: £{mean_val:.2f}",
        )
        plt.axvline(
            median_val,
            color="#5cb85c",
            linestyle="-.",
            linewidth=2,
            label=f"Median Price: £{median_val:.2f}",
        )

        plt.title("Product Price Distribution", fontsize=14, fontweight="bold", pad=12)
        plt.xlabel("Price (£)", fontsize=11, labelpad=8)
        plt.ylabel("Frequency (Product Count)", fontsize=11, labelpad=8)
        plt.grid(axis="y", linestyle=":", alpha=0.6)
        plt.legend(frameon=True, facecolor="#f8f9fa", edgecolor="#ced4da")
        plt.tight_layout()

        plt.savefig(output_path, dpi=300)
        plt.close()
        logger.info("Price distribution chart saved to: %s", output_path)
        return output_path

    def plot_rating_distribution(self, output_path: Path = config.RATING_DIST_CHART_PATH) -> Optional[Path]:
        """
        Generates and saves a bar chart showing the frequency of each star rating.
        """
        ratings_series = self.df["rating"].dropna()
        if ratings_series.empty:
            logger.warning("No rating data available to plot rating distribution.")
            return None

        output_path.parent.mkdir(parents=True, exist_ok=True)
        counts = ratings_series.value_counts().sort_index()

        plt.figure(figsize=(8, 5))
        bar_colors = ["#f39c12", "#e67e22", "#d35400", "#27ae60", "#2980b9"]
        colors = [bar_colors[int(r) - 1] if 1 <= int(r) <= 5 else "#95a5a6" for r in counts.index]

        bars = plt.bar(
            [f"{int(r)} Star{'s' if int(r) > 1 else ''}" for r in counts.index],
            counts.values,
            color=colors,
            edgecolor="#333333",
            width=0.55,
        )

        # Add data labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.annotate(
                f"{height}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        plt.title("Product Rating Frequency Distribution", fontsize=14, fontweight="bold", pad=12)
        plt.xlabel("Star Rating", fontsize=11, labelpad=8)
        plt.ylabel("Number of Products", fontsize=11, labelpad=8)
        plt.ylim(0, max(counts.values) * 1.15)
        plt.grid(axis="y", linestyle=":", alpha=0.6)
        plt.tight_layout()

        plt.savefig(output_path, dpi=300)
        plt.close()
        logger.info("Rating distribution chart saved to: %s", output_path)
        return output_path

    def plot_price_by_rating(self, output_path: Path = config.PRICE_BY_RATING_CHART_PATH) -> Optional[Path]:
        """
        Generates and saves a bar chart showing the average price across different star ratings.
        """
        valid_df = self.df.dropna(subset=["price", "rating"]).copy()
        if valid_df.empty:
            logger.warning("Insufficient price/rating pairs for price-by-rating plot.")
            return None

        output_path.parent.mkdir(parents=True, exist_ok=True)
        avg_prices = valid_df.groupby("rating")["price"].mean().sort_index()

        plt.figure(figsize=(8, 5))
        bars = plt.bar(
            [f"{int(r)} Star{'s' if int(r) > 1 else ''}" for r in avg_prices.index],
            avg_prices.values,
            color="#16a085",
            edgecolor="#0e6251",
            width=0.55,
        )

        for bar in bars:
            height = bar.get_height()
            plt.annotate(
                f"£{height:.2f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        plt.title("Average Product Price by Star Rating", fontsize=14, fontweight="bold", pad=12)
        plt.xlabel("Star Rating", fontsize=11, labelpad=8)
        plt.ylabel("Average Price (£)", fontsize=11, labelpad=8)
        plt.ylim(0, max(avg_prices.values) * 1.18)
        plt.grid(axis="y", linestyle=":", alpha=0.6)
        plt.tight_layout()

        plt.savefig(output_path, dpi=300)
        plt.close()
        logger.info("Price-by-rating chart saved to: %s", output_path)
        return output_path

    def run_all_visualizations(self) -> Dict[str, Optional[Path]]:
        """
        Generates all configured visualization charts.
        """
        return {
            "price_dist": self.plot_price_distribution(),
            "rating_dist": self.plot_rating_distribution(),
            "price_by_rating": self.plot_price_by_rating(),
        }
