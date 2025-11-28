# src/scraper.py
"""
Google Play Store scraper for Ethiopian banking apps.
Targets: Commercial Bank of Ethiopia, Bank of Abyssinia, Dashen Bank.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
from google_play_scraper import Sort, app, reviews
from tqdm import tqdm

from src.config import APP_IDS, BANK_NAMES, DATA_PATHS, SCRAPING_CONFIG


class _LegacyConfig:
    """Backward-compatible shim exposed as `config` for legacy tests."""

    def __init__(self) -> None:
        self.paths = {"raw_data": DATA_PATHS["raw"]}
        self.apps = {
            code: {"id": app_id, "name": BANK_NAMES[code], "count": SCRAPING_CONFIG["reviews_per_bank"]}
            for code, app_id in APP_IDS.items()
        }


config = _LegacyConfig()


class PlayStoreScraper:
    """Scraper class for Google Play Store reviews."""

    def __init__(self) -> None:
        self.app_ids = APP_IDS
        self.bank_names = BANK_NAMES
        self.reviews_per_bank = SCRAPING_CONFIG["reviews_per_bank"]
        self.lang = SCRAPING_CONFIG["lang"]
        self.country = SCRAPING_CONFIG["country"]
        self.max_retries = SCRAPING_CONFIG["max_retries"]

    def get_app_info(self, app_id: str) -> Dict:
        """Fetch metadata for an app."""
        try:
            info = app(app_id, lang=self.lang, country=self.country)
            return {
                "app_id": app_id,
                "title": info.get("title", "N/A"),
                "score": info.get("score", 0),
                "ratings": info.get("ratings", 0),
                "reviews": info.get("reviews", 0),
                "installs": info.get("installs", "N/A"),
            }
        except Exception as exc:  # noqa: BLE001
            print(f"Error getting app info for {app_id}: {exc}")
            return {}

    def scrape_reviews(self, app_id: str, count: int) -> List[Dict]:
        """Scrape reviews for a single app with retries."""
        print(f"\nScraping reviews for {app_id}…")
        for attempt in range(self.max_retries):
            try:
                result, _ = reviews(
                    app_id,
                    lang=self.lang,
                    country=self.country,
                    sort=Sort.NEWEST,
                    count=count,
                    filter_score_with=None,
                )
                print(f"Successfully scraped {len(result)} reviews")
                return result
            except Exception as exc:  # noqa: BLE001
                print(f"Attempt {attempt + 1} failed: {exc}")
                if attempt < self.max_retries - 1:
                    print("Retrying in 5 seconds…")
                    time.sleep(5)
                else:
                    print("Giving up on this app.")
        return []

    def process_reviews(self, reviews_data: List[Dict], bank_code: str) -> List[Dict]:
        """Transform raw review dicts into a consistent format."""
        return [
            {
                "review_id": r.get("reviewId", ""),
                "review_text": r.get("content", ""),
                "rating": r.get("score", 0),
                "review_date": r.get("at", datetime.now()),
                "user_name": r.get("userName", "Anonymous"),
                "thumbs_up": r.get("thumbsUpCount", 0),
                "reply_content": r.get("replyContent"),
                "bank_code": bank_code,
                "bank_name": self.bank_names[bank_code],
                "app_version": r.get("reviewCreatedVersion", ""),
                "source": "Google Play",
            }
            for r in reviews_data
        ]

    def scrape_all_banks(self) -> pd.DataFrame:
        """Scrape all three banks, save CSVs, and return the dataframe."""
        all_reviews: List[Dict] = []
        app_info_records: List[Dict] = []

        print("=" * 60)
        print("Starting Google Play Store Review Scraper")
        print("=" * 60)

        print("\n[1/2] Fetching app information…")
        for code, app_id in self.app_ids.items():
            print(f"\n{code}: {self.bank_names[code]}")
            info = self.get_app_info(app_id)
            if info:
                info.update({"bank_code": code, "bank_name": self.bank_names[code]})
                app_info_records.append(info)
                print(f"  Rating: {info['score']}, Total reviews: {info['reviews']}")

        if app_info_records:
            os.makedirs(DATA_PATHS["raw"], exist_ok=True)
            pd.DataFrame(app_info_records).to_csv(
                os.path.join(DATA_PATHS["raw"], "app_info.csv"), index=False
            )
            print(f"Saved app info to {DATA_PATHS['raw']}/app_info.csv")

        print("\n[2/2] Scraping reviews…")
        for code, app_id in tqdm(self.app_ids.items(), desc="Banks"):
            raw = self.scrape_reviews(app_id, self.reviews_per_bank)
            processed = self.process_reviews(raw, code)
            all_reviews.extend(processed)
            print(f"Collected {len(processed)} reviews for {self.bank_names[code]}")
            time.sleep(2)

        if not all_reviews:
            print("\nNo reviews collected.")
            return pd.DataFrame()

        df = pd.DataFrame(all_reviews)
        os.makedirs(DATA_PATHS["raw"], exist_ok=True)
        df.to_csv(DATA_PATHS["raw_reviews"], index=False, encoding="utf-8")

        print("\n" + "=" * 60)
        print("Scraping complete!")
        print("=" * 60)
        print(f"Total reviews collected: {len(df)}")
        for code in self.bank_names:
            count = len(df[df["bank_code"] == code])
            print(f"  {self.bank_names[code]}: {count}")
        print(f"\nRaw data saved to {DATA_PATHS['raw_reviews']}")
        return df


class ReviewScraper:
    """Compatibility wrapper used by historical unit tests."""

    def __init__(self) -> None:
        self.sort = Sort.NEWEST
        self.paths = config.paths
        self.apps = config.apps
        self.scraper = PlayStoreScraper()

    def _app_code_from_id(self, app_id: str) -> str:
        for code, candidate in APP_IDS.items():
            if candidate == app_id:
                return code
        raise KeyError(f"Unknown app_id: {app_id}")

    def scrape_reviews(self, app_id: str, app_name: str, count: int, sort: Sort) -> List[Dict]:
        _ = sort  # unused, kept for backwards compatibility
        bank_code = self._app_code_from_id(app_id)
        raw = self.scraper.scrape_reviews(app_id, count)
        return [
            {
                "review": row.get("content", ""),
                "rating": row.get("score", 0),
                "date": row.get("at", datetime.now()),
                "bank": app_name,
                "source": "Google Play Store",
                "review_id": row.get("reviewId", ""),
                "bank_code": bank_code,
            }
            for row in raw
        ]

    def save_raw_data(self, df: pd.DataFrame, filename: str = "reviews_raw.csv") -> Path:
        raw_dir = Path(self.paths.get("raw_data", DATA_PATHS["raw"]))
        raw_dir.mkdir(parents=True, exist_ok=True)
        output = raw_dir / filename
        df.to_csv(output, index=False)
        return output

    def scrape_all_banks(self) -> pd.DataFrame:
        rows: List[Dict] = []
        for meta in self.apps.values():
            rows.extend(self.scrape_reviews(meta["id"], meta["name"], meta["count"], self.sort))
        if not rows:
            return pd.DataFrame(columns=["review", "rating", "date", "bank", "source"])
        df = pd.DataFrame(rows)
        self.save_raw_data(df, filename="reviews_legacy.csv")
        return df

    def display_sample_reviews(self, df: pd.DataFrame, n: int = 3) -> None:
        """Print a few sample reviews per bank."""
        print("\n" + "=" * 60)
        print("Sample reviews")
        print("=" * 60)
        for code in self.bank_names:
            subset = df[df["bank_code"] == code].head(n)
            if subset.empty:
                continue
            print(f"\n{self.bank_names[code]} ({len(subset)} samples):")
            for _, row in subset.iterrows():
                stars = "⭐" * int(row["rating"])
                print(f"- {stars} {row['review_text'][:200]}… [{row['review_date']:%Y-%m-%d}]")


def scrape_all_banks() -> pd.DataFrame:
    scraper = PlayStoreScraper()
    dataset = scraper.scrape_all_banks()
    if not dataset.empty:
        scraper.display_sample_reviews(dataset)
    return dataset


if __name__ == "__main__":
    scrape_all_banks()