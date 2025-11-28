"""
Data Preprocessor for Task 1 - Simplified for Ethiopian Banks
"""
import pandas as pd
import os
import re
from src.config import DATA_PATHS


class ReviewPreprocessor:
    def __init__(self):
        self.input_path = DATA_PATHS['raw_reviews']
        self.output_path = DATA_PATHS['processed_reviews']
        self.df = None

    def load_data(self):
        """Load raw data"""
        try:
            self.df = pd.read_csv(self.input_path)
            print(f"✅ Loaded {len(self.df)} raw reviews")
            print(f"📊 Columns found: {list(self.df.columns)}")
            return True
        except FileNotFoundError:
            print(f"❌ Error: Raw data file not found at {self.input_path}")
            return False
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

    def preprocess_data(self):
        """Main preprocessing pipeline for Task 1"""
        print("🔄 Starting data preprocessing...")
        
        # Check what columns we actually have
        print(f"Available columns: {list(self.df.columns)}")
        
        # Remove duplicates
        initial_count = len(self.df)
        if 'review_id' in self.df.columns:
            self.df = self.df.drop_duplicates(subset=['review_id'])
            print(f"🧹 Removed {initial_count - len(self.df)} duplicate reviews")
        else:
            # If no review_id, use combination of text, bank and date
            self.df = self.df.drop_duplicates(subset=['review_text', 'bank_name', 'review_date'])
            print(f"🧹 Removed {initial_count - len(self.df)} duplicate reviews")
        
        # Handle missing data - using ACTUAL column names from your data
        required_columns = ['review_text', 'rating', 'review_date', 'bank_name']
        missing_cols = [col for col in required_columns if col not in self.df.columns]
        
        if missing_cols:
            print(f"❌ Missing required columns: {missing_cols}")
            return None
            
        self.df = self.df.dropna(subset=required_columns)
        print(f"📝 After handling missing data: {len(self.df)} reviews")
        
        # Normalize dates to YYYY-MM-DD
        try:
            self.df['review_date'] = pd.to_datetime(self.df['review_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            # Remove rows with invalid dates
            invalid_dates = self.df['review_date'].isna().sum()
            if invalid_dates > 0:
                print(f"⚠️  Removed {invalid_dates} rows with invalid dates")
                self.df = self.df[self.df['review_date'].notna()]
        except Exception as e:
            print(f"❌ Error processing dates: {e}")
            return None
        
        # Clean text
        self.df['review_text'] = self.df['review_text'].fillna('')
        self.df['review_text'] = self.df['review_text'].apply(
            lambda x: re.sub(r'\s+', ' ', str(x)).strip()
        )
        
        # Remove empty reviews
        empty_reviews = (self.df['review_text'].str.len() == 0).sum()
        if empty_reviews > 0:
            print(f"⚠️  Removed {empty_reviews} empty reviews")
            self.df = self.df[self.df['review_text'].str.len() > 0]
        
        # Validate ratings (1-5)
        invalid_ratings = ((self.df['rating'] < 1) | (self.df['rating'] > 5)).sum()
        if invalid_ratings > 0:
            print(f"⚠️  Removed {invalid_ratings} reviews with invalid ratings")
            self.df = self.df[(self.df['rating'] >= 1) & (self.df['rating'] <= 5)]
        
        # Create final Task 1 format - using the correct column mapping
        processed_df = pd.DataFrame({
            'review': self.df['review_text'],    # Map review_text to review
            'rating': self.df['rating'],
            'date': self.df['review_date'],      # Map review_date to date  
            'bank': self.df['bank_name'],        # Map bank_name to bank
            'source': self.df.get('source', 'Google Play Store')  # Use source if available
        })
        
        print(f"✅ Final processed dataset: {len(processed_df)} reviews")
        return processed_df

    def save_data(self, df):
        """Save processed data"""
        try:
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            df.to_csv(self.output_path, index=False)
            print(f"💾 Saved {len(df)} processed reviews to {self.output_path}")
            
            # Show summary by bank
            print("\n📊 Summary by bank:")
            bank_summary = df.groupby('bank').size()
            for bank, count in bank_summary.items():
                print(f"   {bank}: {count} reviews")
                
            return df
        except Exception as e:
            print(f"❌ Error saving data: {e}")
            return None


def preprocess_reviews():
    """Main preprocessing function"""
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
        print(df[['bank', 'rating', 'date', 'review']].head(3))
    else:
        print("❌ Preprocessing failed!")