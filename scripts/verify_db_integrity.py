"""
Task 3: Verify PostgreSQL database integrity with SQL queries.

This script runs various SQL queries to verify:
- Total review count per bank
- Average ratings per bank
- Sentiment distribution
- Data completeness
"""
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from src.database import DatabaseConnection


def verify_integrity(db: DatabaseConnection) -> bool:
    """Run integrity checks and display results."""
    print("=" * 60)
    print("🔍 Database Integrity Verification")
    print("=" * 60)

    try:
        # 1. Total reviews count
        print("\n📊 [1] Total Reviews Count")
        query = "SELECT COUNT(*) as total FROM reviews"
        result = db.execute_query(query, fetch=True)
        total_reviews = result[0]["total"]
        print(f"   Total reviews in database: {total_reviews:,}")

        if total_reviews < 1000:
            print(f"   ⚠️  Warning: Less than 1,000 reviews (KPI requirement)")

        # 2. Reviews per bank
        print("\n📊 [2] Reviews per Bank")
        query = """
            SELECT b.bank_name, COUNT(r.review_id) as review_count
            FROM banks b
            LEFT JOIN reviews r ON b.bank_id = r.bank_id
            GROUP BY b.bank_id, b.bank_name
            ORDER BY review_count DESC
        """
        results = db.execute_query(query, fetch=True)
        for row in results:
            bank_name = row["bank_name"]
            count = row["review_count"]
            status = "✅" if count >= 400 else "⚠️"
            print(f"   {status} {bank_name}: {count:,} reviews")

        # 3. Average rating per bank
        print("\n⭐ [3] Average Rating per Bank")
        query = """
            SELECT b.bank_name, 
                   ROUND(AVG(r.rating), 2) as avg_rating,
                   MIN(r.rating) as min_rating,
                   MAX(r.rating) as max_rating
            FROM banks b
            JOIN reviews r ON b.bank_id = r.bank_id
            GROUP BY b.bank_id, b.bank_name
            ORDER BY avg_rating DESC
        """
        results = db.execute_query(query, fetch=True)
        for row in results:
            bank_name = row["bank_name"]
            avg_rating = float(row["avg_rating"])
            min_rating = row["min_rating"]
            max_rating = row["max_rating"]
            stars = "⭐" * int(round(avg_rating))
            print(f"   {bank_name}: {avg_rating:.2f} {stars} (range: {min_rating}-{max_rating})")

        # 4. Rating distribution
        print("\n📈 [4] Rating Distribution (Overall)")
        query = """
            SELECT rating, COUNT(*) as count,
                   ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM reviews
            GROUP BY rating
            ORDER BY rating DESC
        """
        results = db.execute_query(query, fetch=True)
        for row in results:
            rating = row["rating"]
            count = row["count"]
            pct = float(row["percentage"])
            stars = "⭐" * rating
            print(f"   {stars} ({rating}): {count:4,} reviews ({pct:5.2f}%)")

        # 5. Sentiment distribution
        print("\n😊 [5] Sentiment Distribution")
        query = """
            SELECT 
                sentiment_label,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage,
                ROUND(AVG(sentiment_score), 4) as avg_score
            FROM reviews
            WHERE sentiment_label IS NOT NULL
            GROUP BY sentiment_label
            ORDER BY count DESC
        """
        results = db.execute_query(query, fetch=True)
        total_with_sentiment = sum(row["count"] for row in results)
        for row in results:
            label = row["sentiment_label"]
            count = row["count"]
            pct = float(row["percentage"])
            avg_score = float(row["avg_score"]) if row["avg_score"] else 0.0
            print(f"   {label:10s}: {count:4,} reviews ({pct:5.2f}%) - Avg score: {avg_score:.4f}")

        sentiment_coverage = (total_with_sentiment / total_reviews * 100) if total_reviews > 0 else 0
        print(f"\n   Sentiment coverage: {sentiment_coverage:.2f}%")
        if sentiment_coverage < 90:
            print(f"   ⚠️  Warning: Sentiment coverage below 90% (Task 2 KPI)")

        # 6. Reviews per rating by bank
        print("\n📊 [6] Rating Distribution by Bank")
        query = """
            SELECT b.bank_name, r.rating, COUNT(*) as count
            FROM banks b
            JOIN reviews r ON b.bank_id = r.bank_id
            GROUP BY b.bank_name, r.rating
            ORDER BY b.bank_name, r.rating DESC
        """
        results = db.execute_query(query, fetch=True)
        current_bank = None
        for row in results:
            bank_name = row["bank_name"]
            rating = row["rating"]
            count = row["count"]
            if bank_name != current_bank:
                if current_bank is not None:
                    print()
                print(f"   {bank_name}:")
                current_bank = bank_name
            stars = "⭐" * rating
            print(f"     {stars}: {count:4,} reviews")

        # 7. Date range
        print("\n📅 [7] Review Date Range")
        query = """
            SELECT 
                MIN(review_date) as earliest_date,
                MAX(review_date) as latest_date,
                COUNT(DISTINCT review_date) as unique_dates
            FROM reviews
        """
        result = db.execute_query(query, fetch=True)
        if result:
            row = result[0]
            print(f"   Earliest review: {row['earliest_date']}")
            print(f"   Latest review: {row['latest_date']}")
            print(f"   Unique dates: {row['unique_dates']}")

        # 8. Data completeness check
        print("\n✅ [8] Data Completeness")
        query = """
            SELECT 
                COUNT(*) as total,
                COUNT(review_text) as has_text,
                COUNT(rating) as has_rating,
                COUNT(review_date) as has_date,
                COUNT(sentiment_label) as has_sentiment_label,
                COUNT(sentiment_score) as has_sentiment_score
            FROM reviews
        """
        result = db.execute_query(query, fetch=True)
        if result:
            row = result[0]
            total = row["total"]
            print(f"   Total reviews: {total:,}")
            print(f"   With review text: {row['has_text']:,} ({row['has_text']/total*100:.1f}%)")
            print(f"   With rating: {row['has_rating']:,} ({row['has_rating']/total*100:.1f}%)")
            print(f"   With date: {row['has_date']:,} ({row['has_date']/total*100:.1f}%)")
            print(
                f"   With sentiment label: {row['has_sentiment_label']:,} ({row['has_sentiment_label']/total*100:.1f}%)"
            )
            print(
                f"   With sentiment score: {row['has_sentiment_score']:,} ({row['has_sentiment_score']/total*100:.1f}%)"
            )

        # Summary
        print("\n" + "=" * 60)
        print("✅ Integrity Check Complete")
        print("=" * 60)

        # KPI Check
        kpi_passed = total_reviews >= 1000
        if kpi_passed:
            print("\n✅ KPI: Database has 1,000+ reviews")
        else:
            print(f"\n⚠️  KPI: Database has {total_reviews} reviews (need 1,000+)")

        return kpi_passed

    except Exception as e:
        print(f"\n❌ Error during integrity check: {e}")
        import traceback

        traceback.print_exc()
        return False


def main() -> None:
    """Main function."""
    db = DatabaseConnection()
    if not db.connect():
        print("❌ Failed to connect to database.")
        print("   Please check your .env file or database credentials.")
        sys.exit(1)

    try:
        success = verify_integrity(db)
        sys.exit(0 if success else 1)
    finally:
        db.disconnect()


if __name__ == "__main__":
    main()

