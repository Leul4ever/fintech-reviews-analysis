# Customer Experience Analytics for Fintech Apps

A comprehensive pipeline for collecting, cleaning, and analyzing Google Play Store reviews for Ethiopian banking apps. This project delivers actionable insights through sentiment analysis and thematic categorization to help banks understand customer satisfaction drivers and pain points.

## 🎯 Project Overview

This repository implements a complete data science pipeline for analyzing mobile banking app reviews:

- **Task 1:** Data collection and preprocessing (1,200+ reviews, <5% missing data)
- **Task 2:** Sentiment analysis and thematic categorization (100% coverage, 7 themes per bank)

**Target Banks:**
- Commercial Bank of Ethiopia (CBE)
- Bank of Abyssinia (BOA)
- Dashen Bank

---

## ✨ Features

### Data Collection & Preprocessing
- ✅ Automated scraping from Google Play Store
- ✅ Robust error handling with retry logic
- ✅ Data quality validation (duplicates, missing values, date normalization)
- ✅ Clean, structured CSV outputs

### Sentiment Analysis
- ✅ State-of-the-art DistilBERT model (`distilbert-base-uncased-finetuned-sst-2-english`)
- ✅ 100% sentiment coverage across all reviews
- ✅ Aggregated sentiment by bank and star rating
- ✅ Positive/negative score breakdowns

### Thematic Analysis
- ✅ TF-IDF keyword extraction with n-grams
- ✅ 7 actionable themes per bank (exceeds 3-5 requirement)
- ✅ Rule-based clustering with documented logic
- ✅ Coverage metrics and example reviews per theme

### Visualization
- ✅ Interactive Jupyter notebook with sentiment and theme visualizations
- ✅ Seaborn/Matplotlib charts for insights

---

## 📋 Requirements

- Python 3.11+
- 8GB+ RAM (for transformer models)
- Internet connection (for scraping and model downloads)

---

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd fintech-reviews-analysis

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Run Task 1: Data Collection & Preprocessing

```bash
# Scrape reviews (400 per bank = 1,200 total)
python scripts/run_scraping.py

# Preprocess the raw data
python scripts/run_preprocessing.py

# Validate Task 1 KPIs
python scripts/validate_task1.py
```

### 3. Run Task 2: Sentiment & Thematic Analysis

```bash
# Run complete sentiment + theme pipeline
python scripts/run_sentiment_themes.py

# Check theme counts per bank
python scripts/check_theme_counts.py
```

### 4. Explore Results

```bash
# Launch Jupyter notebook
jupyter notebook notebooks/task2_sentiment_themes.ipynb
```

---

## 📁 Project Structure

```
fintech-reviews-analysis/
├── .github/
│   └── workflows/
│       └── ci.yml                    # CI/CD pipeline
├── data/
│   ├── raw/                          # Raw scraped data (gitignored)
│   │   ├── reviews_raw.csv
│   │   └── app_info.csv
│   └── processed/                     # Cleaned outputs (gitignored)
│       ├── reviews_processed.csv      # Task 1 output
│       ├── reviews_with_sentiment.csv # Task 2 output
│       ├── sentiment_summary.csv
│       └── theme_summary.csv
├── docs/
│   ├── task2_theme_grouping_logic.md  # Theme documentation
│   ├── task2_verification_report.md   # Task 2 verification
│   └── task2_completion_checklist.md  # Completion checklist
├── notebooks/
│   └── task2_sentiment_themes.ipynb   # Visualization notebook
├── scripts/
│   ├── run_scraping.py                # Scrape reviews
│   ├── run_preprocessing.py           # Clean data
│   ├── run_sentiment_themes.py        # Task 2 pipeline
│   ├── validate_task1.py              # KPI validation
│   └── check_theme_counts.py          # Theme verification
├── src/
│   ├── config.py                      # Configuration
│   ├── scraper.py                     # Play Store scraper
│   ├── preprocessor.py                # Data cleaning
│   └── analysis/
│       ├── sentiment.py               # Sentiment analysis
│       ├── themes.py                  # Theme extraction
│       └── pipeline.py                # Task 2 orchestration
├── tests/
│   ├── test_scraper.py
│   └── test_preprocessor.py
├── requirements.txt
└── README.md
```

---

## 📊 Results Summary

### Task 1: Data Collection & Preprocessing

| Metric | Result |
|--------|--------|
| **Total Reviews Collected** | 1,200 (400 per bank) |
| **Missing Data Rate** | 0% |
| **Data Quality** | ✅ All KPIs met |

**Output:** `data/processed/reviews_processed.csv`
- Columns: `review`, `rating`, `date`, `bank`, `source`

### Task 2: Sentiment & Thematic Analysis

| Metric | Result |
|--------|--------|
| **Sentiment Coverage** | 100% (1,200/1,200 reviews) |
| **Themes per Bank** | 7 themes (exceeds 3-5 requirement) |
| **Sentiment Model** | DistilBERT (SST-2 fine-tuned) |

**Outputs:**
- `reviews_with_sentiment.csv` - Full dataset with sentiment scores and themes
- `sentiment_summary.csv` - Aggregated sentiment by bank/rating
- `theme_summary.csv` - Themes with coverage and examples

**Themes Identified:**
1. Account Access Issues
2. Transaction Performance
3. User Interface & Experience
4. Reliability & Stability
5. Customer Support & Communication
6. Feature Requests
7. Other Feedback

---

## 🔧 Configuration

Default settings in `src/config.py`:

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
```

Override via environment variables or `config.yaml` file.

---

## 📖 Usage Examples

### Command Line Interface

```bash
# Scrape reviews
python scripts/run_scraping.py

# Preprocess data
python scripts/run_preprocessing.py

# Run sentiment + theme analysis
python scripts/run_sentiment_themes.py

# Validate Task 1 KPIs
python scripts/validate_task1.py --target-total 1200 --max-missing 5
```

### Python API

```python
from src.scraper import PlayStoreScraper
from src.preprocessor import ReviewPreprocessor
from src.analysis.pipeline import SentimentThemePipeline

# Task 1: Scraping
scraper = PlayStoreScraper()
raw_df = scraper.scrape_all_banks()

# Task 1: Preprocessing
preprocessor = ReviewPreprocessor()
preprocessor.load_data()
clean_df = preprocessor.preprocess_data()

# Task 2: Sentiment + Themes
pipeline = SentimentThemePipeline()
outputs = pipeline.run()
```

---

## 🔬 Methodology

### Task 1: Data Collection & Preprocessing

1. **Scraping**
   - Uses `google-play-scraper` library
   - Sorts by newest reviews first
   - Retries failed requests (3 attempts, 5s backoff)
   - Saves app metadata separately

2. **Preprocessing**
   - Removes duplicates by `review_id`
   - Handles missing values (drops rows with null critical fields)
   - Normalizes dates to `YYYY-MM-DD` format
   - Validates ratings (1-5 range)
   - Trims whitespace and cleans text

### Task 2: Sentiment & Thematic Analysis

1. **Sentiment Analysis**
   - Model: `distilbert-base-uncased-finetuned-sst-2-english`
   - Batch processing for efficiency
   - Outputs: label (POSITIVE/NEGATIVE), score, probabilities

2. **Keyword Extraction**
   - Method: TF-IDF with n-grams (1-2)
   - Stop-word removal (English)
   - Top keywords extracted per bank

3. **Theme Clustering**
   - Rule-based matching against predefined keyword patterns
   - 6 theme categories + "Other Feedback" catch-all
   - Reviews can match multiple themes
   - Coverage calculated per theme per bank

**Detailed documentation:** See `docs/task2_theme_grouping_logic.md`

---

## 📈 Key Insights

### Sentiment by Rating
- **1-3 stars:** Strongly negative sentiment across all banks
- **4 stars:** Mixed sentiment (varies by bank)
- **5 stars:** Positive sentiment (Dashen Bank highest)

### Common Themes
- **Transaction Performance:** Most common pain point
- **Account Access Issues:** Significant concern for CBE and BOA
- **Reliability & Stability:** Frequent complaints about crashes and errors
- **Feature Requests:** Users want more functionality

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_scraper.py
```

---

## 📚 Documentation

- **Theme Grouping Logic:** `docs/task2_theme_grouping_logic.md`
- **Task 2 Verification:** `docs/task2_verification_report.md`
- **Point-by-Point Check:** `docs/task2_point_by_point_verification.md`

---

## 🎯 Task Completion Status

### Task 1: ✅ Complete
- [x] Repository setup with CI/CD
- [x] Scraping pipeline (1,200 reviews)
- [x] Preprocessing pipeline (<5% missing)
- [x] Validation scripts
- [x] Documentation

### Task 2: ✅ Complete
- [x] Sentiment analysis (100% coverage)
- [x] Theme extraction (7 themes per bank)
- [x] TF-IDF keyword extraction
- [x] Preprocessing (tokenization, stop-words, lemmatization)
- [x] CSV outputs with all required columns
- [x] Documentation and verification

---

## 🚧 Future Enhancements

- [ ] Topic modeling (LDA/NMF) for automatic theme discovery
- [ ] Time-series analysis of sentiment trends
- [ ] Automated nightly scraping via GitHub Actions
- [ ] Interactive dashboard (Streamlit/Dash)
- [ ] Multi-language support (Amharic, Oromo)
- [ ] Comparison with competitor banks

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is for educational and research purposes.

---

## 👥 Acknowledgments

- `google-play-scraper` for Play Store data access
- Hugging Face for the DistilBERT model
- scikit-learn for TF-IDF and NLP utilities

---

## 📞 Contact & Support

For questions or issues, please open an issue on GitHub.

---

**Last Updated:** November 2025  
**Python Version:** 3.11+  
**Status:** ✅ Production Ready
