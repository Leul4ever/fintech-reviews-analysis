"""
Database connection and utilities for PostgreSQL.
"""
import os
from typing import Optional

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Load environment variables from .env file
load_dotenv()


class DatabaseConnection:
    """Manages PostgreSQL database connections."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        """
        Initialize database connection parameters.
        If not provided, reads from environment variables.
        """
        self.host = host or os.getenv("DB_HOST", "localhost")
        self.port = port or int(os.getenv("DB_PORT", "5432"))
        self.database = database or os.getenv("DB_NAME", "bank_reviews")
        self.user = user or os.getenv("DB_USER", "postgres")
        self.password = password or os.getenv("DB_PASSWORD", "")

        self.conn: Optional[psycopg2.extensions.connection] = None

    def connect(self) -> bool:
        """Establish connection to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
            )
            print(f"✅ Connected to PostgreSQL database: {self.database}")
            return True
        except psycopg2.Error as e:
            print(f"❌ Error connecting to database: {e}")
            return False

    def disconnect(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            print("✅ Database connection closed")

    def execute_query(self, query: str, params: Optional[tuple] = None, fetch: bool = False):
        """
        Execute a SQL query.
        
        Args:
            query: SQL query string
            params: Optional parameters for parameterized queries
            fetch: If True, returns fetched results; if False, commits transaction
            
        Returns:
            Query results if fetch=True, None otherwise
        """
        if not self.conn:
            raise ConnectionError("Database connection not established. Call connect() first.")

        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(query, params)
            if fetch:
                results = cursor.fetchall()
                cursor.close()
                return results
            else:
                self.conn.commit()
                cursor.close()
                return None
        except psycopg2.Error as e:
            self.conn.rollback()
            cursor.close()
            raise psycopg2.Error(f"Query execution failed: {e}") from e

    def execute_file(self, filepath: str) -> bool:
        """
        Execute SQL commands from a file.
        
        Args:
            filepath: Path to SQL file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                sql_content = f.read()
            self.execute_query(sql_content)
            print(f"✅ Executed SQL file: {filepath}")
            return True
        except FileNotFoundError:
            print(f"❌ SQL file not found: {filepath}")
            return False
        except Exception as e:
            print(f"❌ Error executing SQL file: {e}")
            return False

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def test_connection() -> bool:
    """Test database connection using environment variables."""
    db = DatabaseConnection()
    if db.connect():
        db.disconnect()
        return True
    return False

