# 1. Imports
import requests
import psycopg2
import os
from dotenv import load_dotenv
import hashlib
import time

# 2. Load environment variables
load_dotenv()
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")

# 3. Function: connect to the database
def connect_db():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

# 4. Checks for data quality
# Check 1: Null Checks
def check_nulls(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM posts
            WHERE reddit_id IS NULL OR title IS NULL OR author_hash IS NULL OR post_date IS NULL OR source IS NULL
        """)
        null_count = cur.fetchone()[0]
        if null_count > 0:
            print(f"Null Check Failed: {null_count} records have null values.")
        else:
            print("Null Check Passed: No null values found.")

# Check 2: Duplicate Checks
def check_duplicates(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT reddit_id, COUNT(*) FROM posts
            GROUP BY reddit_id
            HAVING COUNT(*) > 1 
        """)
        duplicates = cur.fetchall()
        if duplicates:
            print(f"Duplicate Check Failed: Found {len(duplicates)} duplicate reddit_id values.")
        else:
            print("Duplicate Check Passed: No duplicate reddit_id values found.")

# Check 3: Volume checks
def check_volume(conn, expected_count):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM posts WHERE collected_at >= CURRENT_DATE - INTERVAL '1 day'")
        actual_count = cur.fetchone()[0]
        if actual_count < expected_count:
            print(f"Volume Check Failed: Expected at least {expected_count} records, but found {actual_count}.")
        else:
            print(f"Volume Check Passed: Found {actual_count} records, which meets the expected count of {expected_count}.")

# Check 4: Value range checks
def check_value_ranges(conn):
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT COUNT(*) FROM posts
                        WHERE upvote_ratio < 0 OR upvote_ratio > 1 OR post_date > CURRENT_DATE
                    """)
            invalid_count = cur.fetchone()[0]
            if invalid_count > 0:
                print(f"Value Range Check Failed: Found {invalid_count} records with invalid score, upvote_ratio, or post_date values.")
            else:
                print("Value Range Check Passed: All score, upvote_ratio, and post_date values are within valid ranges.")   

# Check 5: Field completeness
def check_field_completeness(conn):
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT COUNT(*) FROM posts
                    """)
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM posts WHERE body IS NULL OR body = ''")
            null_body = cur.fetchone()[0]
            pct = (null_body / total * 100) if total > 0 else 0
            print(f"Field Completeness: {null_body}/{total} posts ({pct:.1f}%) have no body text.")
        
# Print summary of all checks
def run_quality_checks(conn, expected_count):
    print("Running Data Quality Checks...")
    passed = True
    if not check_nulls(conn):
        passed = False
    if not check_duplicates(conn):
        passed = False
    if not check_volume(conn, expected_count):
        passed = False
    if not check_value_ranges(conn):
        passed = False
    if not check_field_completeness(conn):
        passed = False

    return passed

#main function
if __name__ == "__main__":
    conn = connect_db()
    if conn:
        expected_count = 50  # Set your expected count based on your collection goals
        run_quality_checks(conn, expected_count)
        conn.close()
