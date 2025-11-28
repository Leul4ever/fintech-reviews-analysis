"""
Unit tests for the preprocessor module.
"""

import pytest
import pandas as pd
from src.preprocessor import DataPreprocessor


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return pd.DataFrame({
        'review': [
            'Great app!',
            'Love the UI, but it crashes often.',
            'Excellent service',
            'Great app!',  # Duplicate
            '',  # Empty review
            'A' * 100,  # Very long review
        ],
        'rating': [5, 2, 5, 5, 3, 4],
        'date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-15', None, '2024-01-18'],
        'bank': ['CBE', 'BOA', 'Dashen', 'CBE', 'CBE', 'BOA'],
        'source': ['Google Play Store'] * 6,
    })


def test_remove_duplicates(sample_data):
    """Test duplicate removal."""
    preprocessor = DataPreprocessor()
    cleaned = preprocessor.remove_duplicates(sample_data)
    assert len(cleaned) < len(sample_data)


def test_validate_ratings(sample_data):
    """Test rating validation."""
    preprocessor = DataPreprocessor()
    validated = preprocessor.validate_ratings(sample_data)
    assert all(validated['rating'].between(1, 5))


def test_filter_review_length(sample_data):
    """Test review length filtering."""
    preprocessor = DataPreprocessor()
    filtered = preprocessor.filter_review_length(sample_data)
    assert all(filtered['review'].str.len() >= preprocessor.min_review_length)


def test_normalize_dates(sample_data):
    """Test date normalization."""
    preprocessor = DataPreprocessor()
    normalized = preprocessor.normalize_dates(sample_data)
    assert 'date' in normalized.columns


def test_clean_reviews(sample_data):
    """Test complete cleaning pipeline."""
    preprocessor = DataPreprocessor()
    cleaned = preprocessor.clean_reviews(sample_data)
    
    # Check required columns exist
    required_columns = ['review', 'rating', 'date', 'bank', 'source']
    assert all(col in cleaned.columns for col in required_columns)
    
    # Check no duplicates
    assert len(cleaned) == len(cleaned.drop_duplicates(subset=['review', 'rating', 'bank']))

