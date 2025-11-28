# scripts/run_scraping.py
"""
Main script to run scraping for Ethiopian banks
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.scraper import PlayStoreScraper

def main():
    print("🚀 Starting Ethiopian Bank Reviews Scraping")
    scraper = PlayStoreScraper()
    df = scraper.scrape_all_banks()
    if df is not None and not df.empty:
        scraper.display_sample_reviews(df)
    
    if df is not None and not df.empty:
        print("✅ Scraping completed successfully!")
    else:
        print("❌ Scraping failed!")

if __name__ == "__main__":
    main()