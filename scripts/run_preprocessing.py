# scripts/run_preprocessing.py
"""
Main script to run preprocessing
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.preprocessor import preprocess_reviews

def main():
    print("🔄 Starting Data Preprocessing")
    df = preprocess_reviews()
    
    if df is not None and not df.empty:
        print("✅ Preprocessing completed successfully!")
    else:
        print("❌ Preprocessing failed!")

if __name__ == "__main__":
    main()