"""
Data Cleaning and Export Module
Processes raw scraped records into sanitized, structured Pandas DataFrames
and exports them to CSV and Excel formats using OpenPyXL.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

import config

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Cleans, validates, transforms, and exports scraped e-commerce product data.
    """

    EXPECTED_COLUMNS = [
        "product_name",
        "price",
        "rating",
        "availability",
        "product_url",
        "scraped_at",
    ]

    def __init__(self, rating_map: Optional[Dict[str, int]] = None):
        self.rating_map = rating_map or config.RATING_MAP

    def export_raw(self, records: List[Dict[str, Any]], filepath: Path = config.RAW_DATA_PATH) -> Path:
        """
        Saves raw records directly to CSV without transformations.
        Ensures the destination directory exists.
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        df_raw = pd.DataFrame(records)
        df_raw.to_csv(filepath, index=False, encoding="utf-8")
        logger.info("Saved %d raw records to %s", len(df_raw), filepath)
        return filepath

    @staticmethod
    def clean_text(val: Any) -> Optional[str]:
        """
        Strips whitespace, collapses multi-spaces and newlines, and handles None/empty strings.
        """
        if pd.isna(val) or val is None:
            return None
        text = str(val).strip()
        # Collapse internal newlines and repeated whitespace
        text = re.sub(r"\s+", " ", text)
        return text if text else None

    @staticmethod
    def extract_price(val: Any) -> Optional[float]:
        """
        Extracts numeric price from strings like '£51.77', '$19.99', 'Â£10.00'.
        Preserves genuine 0.0 values and maps missing/unparseable values to NaN.
        """
        if pd.isna(val) or val is None:
            return np.nan

        val_str = str(val).strip()
        # Find numeric component (supports integers and decimals)
        match = re.search(r"(\d+(?:\.\d+)?)", val_str)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, TypeError):
                return np.nan
        return np.nan

    def convert_rating(self, val: Any) -> Optional[int]:
        """
        Converts star ratings ('One', 'Two', 'Three', 'Four', 'Five', or digit) to integers 1-5.
        Returns None/NaN if unavailable or unmapped.
        """
        if pd.isna(val) or val is None:
            return None

        val_str = str(val).strip().lower()
        if val_str in self.rating_map:
            return self.rating_map[val_str]

        # Check if already a valid numeric digit
        if val_str.isdigit():
            num = int(val_str)
            if 0 <= num <= 5:
                return num

        return None

    def clean(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Applies a complete cleaning and validation pipeline to raw scraped records:
        - Schema alignment
        - Deduplication
        - Text standardization
        - Price numeric conversion (preserving distinction between 0.0 and NaN)
        - Star rating conversion
        - Filtering of records with missing critical identifiers
        """
        if not records:
            logger.warning("Empty records list provided for cleaning.")
            return pd.DataFrame(columns=self.EXPECTED_COLUMNS)

        df = pd.DataFrame(records)

        # Ensure all expected columns exist
        for col in self.EXPECTED_COLUMNS:
            if col not in df.columns:
                df[col] = np.nan

        initial_count = len(df)
        logger.info("Initiating cleaning pipeline for %d raw records...", initial_count)

        # 1. Deduplication: drop exact duplicates and duplicates by product_url and name
        df = df.drop_duplicates(subset=["product_name", "product_url"], keep="first")
        dedup_count = len(df)
        if initial_count - dedup_count > 0:
            logger.info("Removed %d duplicate records.", initial_count - dedup_count)

        # 2. Text standardization
        df["product_name"] = df["product_name"].apply(self.clean_text)
        df["availability"] = df["availability"].apply(self.clean_text)
        df["product_url"] = df["product_url"].apply(self.clean_text)

        # 3. Numeric price extraction
        df["price"] = df["price"].apply(self.extract_price)

        # 4. Rating conversion to integer
        df["rating"] = df["rating"].apply(self.convert_rating)
        df["rating"] = df["rating"].astype("Int64")  # Pandas nullable integer type

        # 5. Validation: Remove records missing crucial identifier (product_name)
        df = df.dropna(subset=["product_name"])
        df = df[df["product_name"].str.len() > 0]

        # Reorder columns
        df = df[self.EXPECTED_COLUMNS]

        # Reset index
        df = df.reset_index(drop=True)

        logger.info(
            "Cleaning pipeline completed. Valid sanitized records: %d (Dropped: %d)",
            len(df),
            initial_count - len(df),
        )
        return df

    def export_cleaned(
        self,
        df: pd.DataFrame,
        csv_path: Path = config.CLEANED_DATA_PATH,
        excel_path: Path = config.EXCEL_DATA_PATH,
    ) -> None:
        """
        Exports cleaned DataFrame to CSV and formatted Excel workbook.
        """
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        excel_path.parent.mkdir(parents=True, exist_ok=True)

        # Export CSV
        df.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info("Cleaned CSV exported to: %s", csv_path)

        # Export formatted Excel using openpyxl
        try:
            with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Products", index=False)
                worksheet = writer.sheets["Products"]

                # Apply basic formatting (auto column width, styled headers)
                from openpyxl.styles import Alignment, Font, PatternFill

                header_fill = PatternFill(
                    start_color="1F497D", end_color="1F497D", fill_type="solid"
                )
                header_font = Font(color="FFFFFF", bold=True, size=11)

                for col_idx, column in enumerate(worksheet.columns, start=1):
                    # Style header row
                    cell = worksheet.cell(row=1, column=col_idx)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")

                    # Compute reasonable column width
                    max_len = max(len(str(cell.value or "")) for cell in column)
                    col_letter = worksheet.cell(row=1, column=col_idx).column_letter
                    worksheet.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 60)

            logger.info("Cleaned Excel workbook exported to: %s", excel_path)
        except Exception as err:
            logger.error("Failed to write styled Excel file: %s", err, exc_info=True)
            # Fallback to basic export if styling fails
            df.to_excel(excel_path, index=False)
