"""
Task 3: Load cleaned review data into PostgreSQL database.

This script:
1. Reads processed reviews from CSV (with sentiment data if available)
2. Creates/updates banks table
3. Inserts reviews into PostgreSQL database
4. Handles duplicates and data validation
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from src.database import DatabaseConnection


def load_banks(db: DatabaseConnection, df: pd.DataFrame) -> dict[str, int]:
    """
    Load unique banks into the banks table and return bank_name -> bank_id mapping.
    
    Args:
        db: Database connection
        df: DataFrame containing bank data
        
    Returns:
        Dictionary mapping bank_name to bank_id
    """
    bank_names = df["bank"].unique()
    bank_mapping: dict[str, int] = {}

    print("\n📊 Loading banks into database...")
    for bank_name in bank_names:
        # Check if bank exists
        check_query = "SELECT bank_id FROM banks WHERE bank_name = %s"
        existing = db.execute_query(check_query, (bank_name,), fetch=True)

        if existing:
            bank_id = existing[0]["bank_id"]
            print(f"  ✓ Bank already exists: {bank_name} (ID: {bank_id})")
        else:
            # Insert new bank
            # Extract app name from bank name (simplified)
            app_name = f"{bank_name} Mobile Banking"
            insert_query = """
                INSERT INTO banks (bank_name, app_name)
                VALUES (%s, %s)
                RETURNING bank_id
            """
            result = db.execute_query(insert_query, (bank_name, app_name), fetch=True)
            bank_id = result[0]["bank_id"]
            print(f"  ✓ Added new bank: {bank_name} (ID: {bank_id})")

        bank_mapping[bank_name] = bank_id

    return bank_mapping


def load_reviews(
    db: DatabaseConnection, df: pd.DataFrame, bank_mapping: dict[str, int]
) -> tuple[int, int]:
    """
    Load reviews into the reviews table.
    
    Args:
        db: Database connection
        df: DataFrame containing review data
        bank_mapping: Dictionary mapping bank_name to bank_id
        
    Returns:
        Tuple of (inserted_count, skipped_count)
    """
    print("\n📝 Loading reviews into database...")

    inserted_count = 0
    skipped_count = 0

    # Prepare insert query
    insert_query = """
        INSERT INTO reviews (
            review_id, bank_id, review_text, rating, review_date,
            sentiment_label, sentiment_score, source
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (review_id) DO UPDATE SET
            review_text = EXCLUDED.review_text,
            rating = EXCLUDED.rating,
            review_date = EXCLUDED.review_date,
            sentiment_label = EXCLUDED.sentiment_label,
            sentiment_score = EXCLUDED.sentiment_score,
            source = EXCLUDED.source
    """

    for _, row in df.iterrows():
        try:
            bank_name = row["bank"]
            bank_id = bank_mapping.get(bank_name)

            if not bank_id:
                print(f"  ⚠️  Skipping review: Bank '{bank_name}' not found in mapping")
                skipped_count += 1
                continue

            # Extract data with defaults
            review_id = str(row.get("review_id", ""))
            review_text = str(row.get("review", row.get("review_text", "")))
            rating = int(row.get("rating", 1))
            review_date = pd.to_datetime(row.get("date", row.get("review_date"))).date()
            sentiment_label = row.get("sentiment_label")
            sentiment_score = (
                float(row.get("sentiment_score")) if pd.notna(row.get("sentiment_score")) else None
            )
            source = str(row.get("source", "Google Play"))

            # Validate required fields
            if not review_id or not review_text or pd.isna(review_date):
                skipped_count += 1
                continue

            # Execute insert
            db.execute_query(
                insert_query,
                (
                    review_id,
                    bank_id,
                    review_text,
                    rating,
                    review_date,
                    sentiment_label,
                    sentiment_score,
                    source,
                ),
            )
            inserted_count += 1

            if inserted_count % 100 == 0:
                print(f"  ✓ Inserted {inserted_count} reviews...")

        except Exception as e:
            print(f"  ⚠️  Error inserting review {row.get('review_id', 'unknown')}: {e}")
            skipped_count += 1
            continue

    return inserted_count, skipped_count


def main() -> None:
    """Main function to load data into PostgreSQL."""
    parser = argparse.ArgumentParser(
        description="Load processed review data into PostgreSQL database."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/reviews_with_sentiment.csv",
        help="Path to processed reviews CSV file (with sentiment if available).",
    )
    parser.add_argument(
        "--schema",
        type=str,
        default="database/schema.sql",
        help="Path to SQL schema file.",
    )
    parser.add_argument(
        "--create-tables",
        action="store_true",
        help="Create database tables before loading data (drops existing tables).",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 Task 3: Loading Data into PostgreSQL")
    print("=" * 60)

    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"❌ Error: Input file not found: {args.input}")
        print("   Run preprocessing and sentiment analysis first:")
        print("   python scripts/run_preprocessing.py")
        print("   python scripts/run_sentiment_themes.py")
        sys.exit(1)

    # Connect to database
    db = DatabaseConnection()
    if not db.connect():
        print("\n❌ Failed to connect to database.")
        print("   Please check your .env file or database credentials.")
        sys.exit(1)

    try:
        # Create tables if requested
        if args.create_tables:
            print("\n📋 Creating database schema...")
            if os.path.exists(args.schema):
                db.execute_file(args.schema)
            else:
                print(f"⚠️  Schema file not found: {args.schema}")
                print("   Tables may already exist or need to be created manually.")

        # Load data
        print(f"\n📂 Reading data from: {args.input}")
        df = pd.read_csv(args.input)

        # Handle column name variations
        column_mapping = {
            "review_text": "review",
            "review_date": "date",
            "bank_name": "bank",
        }
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df[new_col] = df[old_col]

        # Ensure required columns exist
        required_cols = ["bank", "review", "rating", "date"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"❌ Missing required columns: {missing_cols}")
            sys.exit(1)

        print(f"✅ Loaded {len(df)} reviews from CSV")

        # Load banks first
        bank_mapping = load_banks(db, df)

        # Load reviews
        inserted, skipped = load_reviews(db, df, bank_mapping)

        print("\n" + "=" * 60)
        print("✅ Data Loading Complete!")
        print("=" * 60)
        print(f"📊 Total reviews processed: {len(df)}")
        print(f"✅ Reviews inserted/updated: {inserted}")
        print(f"⚠️  Reviews skipped: {skipped}")
        print(f"🏦 Banks in database: {len(bank_mapping)}")

    except Exception as e:
        print(f"\n❌ Error during data loading: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    finally:
        db.disconnect()


if __name__ == "__main__":
    main()

