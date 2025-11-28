# src/config.py
"""
Configuration for Task 1 - Ethiopian Banks
UPDATED WITH YOUR SPECIFIC BANKS
"""

# Your Ethiopian bank app IDs - UPDATED HERE
APP_IDS = {
    'CBE': 'com.combanketh.mobilebanking',
    'BOA': 'com.boa.boaMobileBanking', 
    'DASHEN': 'com.dashen.dashensuperapp'
}

# Bank Names Mapping
BANK_NAMES = {
    'CBE': 'Commercial Bank of Ethiopia',
    'BOA': 'Bank of Abyssinia',
    'DASHEN': 'Dashen Bank'
}

# Scraping Configuration
SCRAPING_CONFIG = {
    'reviews_per_bank': 400,
    'max_retries': 3,
    'lang': 'en',
    'country': 'et'  # Ethiopia
}

# File Paths
DATA_PATHS = {
    'raw': 'data/raw',
    'processed': 'data/processed',
    'raw_reviews': 'data/raw/reviews_raw.csv',
    'processed_reviews': 'data/processed/reviews_processed.csv'
}