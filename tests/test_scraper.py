"""
Unit tests for scraper utilities.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.scraper import ReviewScraper
from src import scraper as scraper_module


def test_save_raw_data_creates_file(tmp_path, monkeypatch):
    monkeypatch.setitem(scraper_module.config.paths, "raw_data", str(tmp_path))
    scraper = ReviewScraper()
    df = pd.DataFrame(
        [
            {"review": "Great", "rating": 5, "date": "2024-01-01", "bank": "Test", "source": "Google Play Store"},
        ]
    )
    output = scraper.save_raw_data(df, filename="test_raw.csv")
    assert output.exists()
    assert output.read_text().strip() != ""


def test_scrape_all_banks_uses_config(monkeypatch):
    def fake_scrape_reviews(self, app_id, app_name, count, sort):
        return [
            {
                "review": f"{app_name} works",
                "rating": 5,
                "date": "2024-01-01",
                "bank": app_name,
                "source": "Google Play Store",
            }
        ]

    monkeypatch.setattr(ReviewScraper, "scrape_reviews", fake_scrape_reviews)
    scraper = ReviewScraper()
    df = scraper.scrape_all_banks()
    assert set(df["bank"].unique()) == {cfg["name"] for cfg in scraper_module.config.apps.values()}
    assert len(df) == len(scraper_module.config.apps)

