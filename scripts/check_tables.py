"""
Quick script to verify tables exist in the database.
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from src.database import DatabaseConnection

def main():
    db = DatabaseConnection()
    if not db.connect():
        print("❌ Failed to connect to database")
        sys.exit(1)
    
    try:
        result = db.execute_query(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
            ('public',),
            fetch=True
        )
        print("\n📊 Tables in database:")
        for row in result:
            print(f"  ✅ {row['table_name']}")
        
        # Check column details
        print("\n📋 Banks Table Columns:")
        result = db.execute_query(
            """SELECT column_name, data_type, is_nullable 
               FROM information_schema.columns 
               WHERE table_name = 'banks' 
               ORDER BY ordinal_position""",
            fetch=True
        )
        for row in result:
            nullable = "NULL" if row['is_nullable'] == 'YES' else "NOT NULL"
            print(f"  - {row['column_name']}: {row['data_type']} ({nullable})")
        
        print("\n📋 Reviews Table Columns:")
        result = db.execute_query(
            """SELECT column_name, data_type, is_nullable 
               FROM information_schema.columns 
               WHERE table_name = 'reviews' 
               ORDER BY ordinal_position""",
            fetch=True
        )
        for row in result:
            nullable = "NULL" if row['is_nullable'] == 'YES' else "NOT NULL"
            print(f"  - {row['column_name']}: {row['data_type']} ({nullable})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        db.disconnect()

if __name__ == "__main__":
    main()

