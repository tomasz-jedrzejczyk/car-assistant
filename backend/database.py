import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Database Configuration ───────────────────────────────────

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# ─── Database Connection Pool ────────────────────────────────

class DatabaseConnection:
    """
    Manages PostgreSQL connections.
    Use this to query the database from API endpoints.
    """
    
    def __init__(self):
        self.connection = None
    
    def connect(self):
        """Establish connection to PostgreSQL"""
        try:
            self.connection = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            print(f"✅ Connected to database: {DB_NAME}")
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("Database connection closed")
    
    @contextmanager
    def get_cursor(self, commit: bool = True) -> Generator:
        """
        Context manager for database queries.
        
        Usage:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM users")
                results = cursor.fetchall()
        """
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            if commit:
                self.connection.commit()
        except psycopg2.Error as e:
            self.connection.rollback()
            print(f"Database error: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_query(self, query: str, params: tuple = None) -> list:
        """Execute a SELECT query and return results"""
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    
    def execute_insert(self, query: str, params: tuple = None) -> dict:
        """Execute an INSERT query and return the inserted row"""
        with self.get_cursor(commit=True) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an UPDATE query and return rows affected"""
        with self.get_cursor(commit=True) as cursor:
            cursor.execute(query, params or ())
            return cursor.rowcount
    
    def execute_delete(self, query: str, params: tuple = None) -> int:
        """Execute a DELETE query and return rows deleted"""
        with self.get_cursor(commit=True) as cursor:
            cursor.execute(query, params or ())
            return cursor.rowcount


# ─── Initialize database connection ───────────────────────────
# This gets created once when the app starts

db = DatabaseConnection()