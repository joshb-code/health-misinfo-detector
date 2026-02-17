# 1. Imports
import re
import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

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

# 4. Function: text cleaning
def clean_text(text):
    # Handle None values
    if text is None:
        return ""
    # Basic cleaning: lowercase and remove extra whitespace
    cleaned = text.lower().strip()
    # Remove URLs
    cleaned = re.sub(r'http\S+', '', cleaned).strip()
    # Remove special characters (keep letters, numbers, spaces)
    cleaned = re.sub(r'[^a-z0-9\s]', '', cleaned).strip()
    return cleaned

# 5. function: Metadata feature engineering
def metadata_features(post_id, title, body):
        raw_text = title + " " + (body or "")
        text_no_spaces = raw_text.replace(" ", "")
        features = {
            "word_count": len(raw_text.split()),
            "char_count": len(raw_text),
            "has_url": 1 if re.search(r'http\S+', raw_text) else 0,
            "caps_ratio": sum(1 for c in text_no_spaces if c.isupper()) / len(text_no_spaces) if text_no_spaces else 0,
            "exclamation_count": raw_text.count("!"),
            "question_count": raw_text.count("?")
        }
        return features


# Main
if __name__ == "__main__":
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT post_id, title, body FROM posts")
        posts = cursor.fetchall()

        processed_posts = []
        for post_id, title, body in posts:
            cleaned_title = clean_text(title)
            cleaned_body = clean_text(body)
            combined_text = f"{cleaned_title} {cleaned_body}".strip()
            features = metadata_features(post_id, title, body)
            processed_posts.append({
                "post_id": post_id,
                "cleaned_title": cleaned_title,
                "cleaned_body": cleaned_body,
                "combined_text": combined_text,
                **features
            })
        # Save processed_posts to CSV
        df = pd.DataFrame(processed_posts)
        df.to_csv("data/processed_posts.csv", index=False)
        cursor.close()
        conn.close()


    