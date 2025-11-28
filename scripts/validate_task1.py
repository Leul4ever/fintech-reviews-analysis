# scripts/validate_task1.py
"""
Validate Task 1 requirements
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from src.config import DATA_PATHS

def validate_task1():
    """Validate Task 1 KPIs"""
    try:
        df = pd.read_csv(DATA_PATHS['processed_reviews'])
        
        print("📊 TASK 1 VALIDATION")
        print("=" * 50)
        
        # Check requirements
        total = len(df)
        total_ok = total >= 1200
        
        banks_ok = True
        print("Reviews per bank:")
        for bank in ['Commercial Bank of Ethiopia', 'Bank of Abyssinia', 'Dashen Bank']:
            count = len(df[df['bank'] == bank])
            ok = count >= 400
            banks_ok = banks_ok and ok
            print(f"  {bank}: {count}/400 {'✅' if ok else '❌'}")
        
        missing_ok = df.isnull().sum().sum() == 0
        cols_ok = set(['review', 'rating', 'date', 'bank', 'source']).issubset(df.columns)
        
        print(f"\nTotal reviews: {total}/1200 {'✅' if total_ok else '❌'}")
        print(f"No missing data: {'✅' if missing_ok else '❌'}")
        print(f"Correct columns: {'✅' if cols_ok else '❌'}")
        
        all_ok = all([total_ok, banks_ok, missing_ok, cols_ok])
        print(f"\nOverall: {'✅ ALL REQUIREMENTS MET' if all_ok else '❌ REQUIREMENTS NOT MET'}")
        
        return all_ok
        
    except FileNotFoundError:
        print("❌ Processed data file not found. Run preprocessing first.")
        return False

if __name__ == "__main__":
    validate_task1()