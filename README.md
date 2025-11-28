# Customer Experience Analytics for Fintech Apps

Collect, clean, and analyze Google Play Store reviews for Commercial Bank of Ethiopia (CBE), Bank of Abyssinia (BOA), and Dashen Bank. Task 1 focuses on delivering a reproducible scraping + preprocessing pipeline that satisfies the KPI targets (≥400 reviews per bank, ≥1,200 total, <5 % missing) and documents the methodology.

---

## 1. Repository Layout

```
fintech-reviews-analysis/
├── .github/workflows/ci.yml        # Smoke tests on pull requests
├── data/
│   ├── raw/                        # Raw CSV exports (ignored by git)
│   └── processed/                  # Cleaned CSV outputs (ignored by git)
├── notebooks/                      # Optional EDA summaries
├── scripts/                        # CLI entry-points (scrape, preprocess, validate)
├── src/                            # Core scraper & preprocessor modules
├── tests/                          # Unit tests for Task 1 utilities
├── requirements.txt
└── README.md
```

`data/*` directories are kept out of version control via `.gitignore` so large CSVs remain local.

---

## 2. Environment Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install --upgrade pip
pip install -r requirements.txt
```

Dependencies: `google-play-scraper`, `pandas`, `numpy`, `tqdm`.

---

## 3. Configuration

Defaults live in `src/config.py`:

```python
APP_IDS = {
    "CBE": "com.combanketh.mobilebanking",
    "BOA": "com.boa.boaMobileBanking",
    "DASHEN": "com.dashen.dashensuperapp",
}
SCRAPING_CONFIG = {
    "reviews_per_bank": 400,
    "max_retries": 3,
    "lang": "en",
    "country": "et",
}
DATA_PATHS = {
    "raw_reviews": "data/raw/reviews_raw.csv",
    "processed_reviews": "data/processed/reviews_processed.csv",
}
```

Override any key via environment variables (`CBE_APP_ID`, `SCRAPING__REVIEWS_PER_BANK`, etc.) or by adding a `config.yaml` with matching keys.

---

## 4. Pipelines & CLI Commands

Run all commands from the project root so `python -m` can resolve packages.

| Step | Purpose | Command |
|------|---------|---------|
| Scrape | Pull ≥400 reviews per bank into `data/raw/reviews_raw.csv` | `python -m scripts.run_scraping --per-app 450` |
| Preprocess | Clean the latest raw CSV and write `data/processed/reviews_processed.csv` | `python -m scripts.run_preprocessing` |
| Validate | Confirm Task 1 KPIs (coverage, columns, missing data) | `python -m scripts.validate_task1 --target-total 1200 --max-missing 5` |
| Tests | Run scraper/preprocessor unit tests | `pytest` |

Both scraping and preprocessing scripts can accept optional `--input/--output` arguments if you want to point at specific files.

---

## 5. Methodology Summary (Task 1)

1. **Scraping** (`scripts/run_scraping.py` → `src/scraper.py`)
   - Uses `google_play_scraper` with newest-first sorting to capture the most recent feedback.
   - Retries failed network calls up to 3 times with a 5 s back-off.
   - Stores per-app metadata in `data/raw/app_info.csv`.

2. **Preprocessing** (`scripts/run_preprocessing.py` → `src/preprocessor.py`)
   - Loads the raw CSV, deduplicates by `review_id`, enforces non-null `review`, `rating`, `date`, `bank`.
   - Normalizes timestamps to `YYYY-MM-DD` and trims whitespace.
   - Filters invalid ratings (must be between 1 and 5) and outputs Task 1 schema: `review, rating, date, bank, source`.

3. **Validation** (`scripts/validate_task1.py`)
   - Checks review counts per bank, overall total, column presence, and missing-value ratio to guarantee KPI compliance.

---

## 6. Task 1 Results (2025‑11‑28 Run)

| Metric | Result |
|--------|--------|
| Total raw reviews collected | **1,200** (400 per bank) |
| Total cleaned reviews | **1,200** |
| Missing-value ratio after preprocessing | **0 %** |
| Output columns | `review`, `rating`, `date`, `bank`, `source` |
| Raw output location | `data/raw/reviews_raw.csv` |
| Processed output location | `data/processed/reviews_processed.csv` |

Breakdown by bank (after cleaning):
- Commercial Bank of Ethiopia: 400 reviews
- Bank of Abyssinia: 400 reviews
- Dashen Bank: 400 reviews

`python -m scripts.validate_task1 --target-total 1200 --max-missing 5` prints the same summary and confirms “✅ ALL REQUIREMENTS MET”.

---

## 7. Direct Module Usage

```python
from src.scraper import PlayStoreScraper
from src.preprocessor import ReviewPreprocessor

scraper = PlayStoreScraper()
raw_df = scraper.scrape_all_banks()

preprocessor = ReviewPreprocessor()
preprocessor.load_data()           # reads DATA_PATHS['raw_reviews']
clean_df = preprocessor.preprocess_data()
```

Use this approach inside notebooks or other orchestration scripts when you need programmatic access instead of the CLI wrappers.

---

## 8. Task 1 Checklist

- [x] Repository + CI skeleton (`.gitignore`, `requirements.txt`, GitHub Actions).
- [x] Configured scraper with retry/backoff targeting the latest Play Store IDs.
- [x] Deterministic preprocessing pipeline with data-quality reporting.
- [x] Command wrappers for scraping, preprocessing, and KPI validation.
- [x] Tests for scraper and preprocessor utilities.
- [x] Gathered ≥400 reviews per bank (1,200 total) and stored raw CSV outputs.
- [x] Produced a cleaned CSV (<5 % missing) and documented methodology/results in this README.

---

## 9. Next Steps

- Incorporate sentiment or topic modeling analyses (Task 2+).
- Automate nightly scraping via GitHub Actions + secure secrets.
- Publish aggregate dashboards that consume `data/processed/reviews_processed.csv`.

Task 1 deliverables are complete and validated; future work can build directly on the reproducible pipeline captured here.

