"""
Data preprocessor utilities and CLI pipeline for Task 1.
"""

from __future__ import annotations

import os
import pandas as pd

from src.config import DATA_PATHS


class DataPreprocessor:
    """Reusable text-cleaning utilities used by both tests and CLI."""

    def __init__(self, min_review_length: int = 3) -> None:
        self.min_review_length = min_review_length

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        subset = ["review_id"] if "review_id" in df.columns else ["review", "rating", "bank"]
        return df.drop_duplicates(subset=subset).reset_index(drop=True)

    def validate_ratings(self, df: pd.DataFrame) -> pd.DataFrame:
        filtered = df[df["rating"].between(1, 5)]
        return filtered.dropna(subset=["rating"]).reset_index(drop=True)

    def filter_review_length(self, df: pd.DataFrame) -> pd.DataFrame:
        reviews = df["review"].fillna("").astype(str)
        mask = reviews.str.len() >= self.min_review_length
        filtered = df[mask].copy()
        filtered["review"] = reviews[mask]
        return filtered.reset_index(drop=True)

    def normalize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        normalized = df.copy()
        normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce")
        normalized = normalized.dropna(subset=["date"])
        normalized["date"] = normalized["date"].dt.strftime("%Y-%m-%d")
        return normalized.reset_index(drop=True)

    def clean_reviews(self, df: pd.DataFrame, keep_columns: list[str] | None = None) -> pd.DataFrame:
        cleaned = df.copy()
        keep_columns = keep_columns or []
        cleaned["review"] = (
            cleaned["review"]
            .fillna("")
            .astype(str)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        cleaned["source"] = cleaned.get("source", "Google Play").fillna("Google Play")

        cleaned = cleaned.dropna(subset=["bank"])
        cleaned = self.remove_duplicates(cleaned)
        cleaned = self.validate_ratings(cleaned)
        cleaned = self.normalize_dates(cleaned)
        cleaned = self.filter_review_length(cleaned)
        cleaned = cleaned[cleaned["review"].str.len() > 0]

        required_columns = ["review", "rating", "date", "bank", "source"]
        missing = [col for col in required_columns if col not in cleaned.columns]
        if missing:
            raise ValueError(f"Missing required columns after cleaning: {missing}")

        final_columns = required_columns + [col for col in keep_columns if col in cleaned.columns]
        return cleaned[final_columns].reset_index(drop=True)


class ReviewPreprocessor:
    """File-based wrapper that reads raw CSVs and applies DataPreprocessor."""

    def __init__(self) -> None:
        self.input_path = DATA_PATHS["raw_reviews"]
        self.output_path = DATA_PATHS["processed_reviews"]
        self.df: pd.DataFrame | None = None

    def load_data(self) -> bool:
        try:
            self.df = pd.read_csv(self.input_path)
            print(f"✅ Loaded {len(self.df)} raw reviews")
            print(f"📊 Columns found: {list(self.df.columns)}")
            return True
        except FileNotFoundError:
            print(f"❌ Error: Raw data file not found at {self.input_path}")
            return False
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Error loading data: {exc}")
            return False

    def preprocess_data(self) -> pd.DataFrame | None:
        if self.df is None:
            print("❌ No data loaded. Call load_data() first.")
            return None

        print("🔄 Starting data preprocessing...")
        cleaner = DataPreprocessor()

        df = self.df.copy()
        rename_map = {
            "review_text": "review",
            "review_date": "date",
            "bank_name": "bank",
        }
        df = df.rename(columns=rename_map)

        if "bank" not in df.columns and "bank_name" in self.df.columns:
            df["bank"] = self.df["bank_name"]
        if "source" not in df.columns:
            df["source"] = self.df.get("source", "Google Play Store")

        required = {"review", "rating", "date", "bank"}
        missing = [col for col in required if col not in df.columns]
        if missing:
            print(f"❌ Missing required columns: {missing}")
            return None

        keep_columns = [col for col in ["review_id", "bank_code", "user_name"] if col in df.columns]
        processed_df = cleaner.clean_reviews(df, keep_columns=keep_columns)
        print(f"✅ Final processed dataset: {len(processed_df)} reviews")
        return processed_df

    def save_data(self, df: pd.DataFrame) -> pd.DataFrame | None:
        try:
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            df.to_csv(self.output_path, index=False)
            print(f"💾 Saved {len(df)} processed reviews to {self.output_path}")

            print("\n📊 Summary by bank:")
            summary = df.groupby("bank").size()
            for bank, count in summary.items():
                print(f"   {bank}: {count} reviews")
            return df
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Error saving data: {exc}")
            return None


def preprocess_reviews() -> pd.DataFrame | None:
    preprocessor = ReviewPreprocessor()
    if not preprocessor.load_data():
        return None
    processed_df = preprocessor.preprocess_data()
    if processed_df is not None:
        preprocessor.save_data(processed_df)
    return processed_df


if __name__ == "__main__":
    df = preprocess_reviews()
    if df is not None:
        print(f"\n🎉 Preprocessing completed! Final dataset: {len(df)} reviews")
        print("\n📋 Sample of processed data:")
        print(df[["bank", "rating", "date", "review"]].head(3))
    else:
        print("❌ Preprocessing failed!")