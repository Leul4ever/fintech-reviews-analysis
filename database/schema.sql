-- Task 3: PostgreSQL Database Schema for Bank Reviews
-- Database: bank_reviews

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS banks CASCADE;

-- Banks Table
-- Stores information about the banks
CREATE TABLE banks (
    bank_id SERIAL PRIMARY KEY,
    bank_name VARCHAR(255) NOT NULL UNIQUE,
    app_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reviews Table
-- Stores the scraped and processed review data
CREATE TABLE reviews (
    review_id VARCHAR(255) PRIMARY KEY,
    bank_id INTEGER NOT NULL REFERENCES banks(bank_id) ON DELETE CASCADE,
    review_text TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_date DATE NOT NULL,
    sentiment_label VARCHAR(20),
    sentiment_score DECIMAL(10, 6),
    source VARCHAR(100) DEFAULT 'Google Play',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX idx_reviews_bank_id ON reviews(bank_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_date ON reviews(review_date);
CREATE INDEX idx_reviews_sentiment_label ON reviews(sentiment_label);
CREATE INDEX idx_banks_bank_name ON banks(bank_name);

-- Comments for documentation
COMMENT ON TABLE banks IS 'Stores information about Ethiopian banks';
COMMENT ON TABLE reviews IS 'Stores scraped and processed Google Play Store reviews with sentiment analysis';
COMMENT ON COLUMN reviews.sentiment_label IS 'Sentiment classification: POSITIVE, NEGATIVE, or NEUTRAL';
COMMENT ON COLUMN reviews.sentiment_score IS 'Sentiment score from DistilBERT model (range: -1.0 to 1.0)';

