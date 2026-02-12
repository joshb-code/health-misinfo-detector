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

# 4. Function: fetch posts from Reddit
#    - Takes a subreddit name and a search term
#    - Hits https://www.reddit.com/r/{subreddit}/search.json?q={search_term}&restrict_sr=on&limit=100
#    - Returns a list of post dictionaries
def fetch_reddit_posts(subreddit, search_term):
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {
        "q": search_term,
        "restrict_sr": "on",
        "limit": 100
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; RedditPostCollector/1')"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        posts = []
        for item in data.get("data", {}).get("children", []):
            post_data = item.get("data", {})
            post = {
                "reddit_id": post_data.get("id"),
                "title": post_data.get("title"),
                "author": post_data.get("author"),
                "post_date": post_data.get("created_utc"),
                "source": subreddit,
                "search_term": search_term,
                "body": post_data.get("selftext"),
                "score": post_data.get("score"),
                "num_comments": post_data.get("num_comments"),
                "upvote_ratio": post_data.get("upvote_ratio"),
                "flair": post_data.get("link_flair_text")
            }
            posts.append(post)
        return posts
    except Exception as e:
        print(f"Error fetching posts from Reddit: {e}")
        return []
    
# 5. Function: insert a post into the database
#    - Takes a database connection and a post dictionary
#    - Hashes the author name
#    - Inserts into the posts table
#    - Handles duplicates (what happens if reddit_id already exists?)
def insert_post(conn, post):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                        INSERT INTO POSTS (reddit_id, source, title, body, author_hash, score, num_comments, upvote_ratio, flair, post_date,  searchterm)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, to_timestamp(%s), %s)
                        ON CONFLICT (reddit_id) DO NOTHING -- Skip duplicates
                        """,
                        (
                            post["reddit_id"],
                            post["source"],
                            post["title"],
                            post["body"],
                            hash_author(post["author"]), 
                            post["score"],
                            post["num_comments"],
                            post["upvote_ratio"],
                            post["flair"],
                            post["post_date"],
                            post["search_term"]
                        )
            )
        conn.commit()
    except Exception as e:
        print(f"Error inserting post into database: {e}")
        conn.rollback()
    
# Helper function to hash author names (for anonymization)
def hash_author(author_name):
    if author_name is None:
        return None
    return hashlib.sha256(author_name.encode('utf-8')).hexdigest()

# 6. Main block
#    - Define your list of subreddits and search terms
#    - Connect to DB
#    - Loop through each subreddit + search term combo
#    - Fetch posts, insert each one
#    - Print how many were collected
if __name__ == "__main__":
    subreddits = ["nutrition", "supplements", "fitness", "loseit", "ScientificNutrition", "AlternativeHealth", "Nootropics"]
    search_terms = ["detox", "superfood", "fat burner", "miracle cure", "apple cider vinegar", "natural remedy", "cleanses toxins", "supplement stack"]

    conn = connect_db()
    if conn is None:
        print("Failed to connect to database. Exiting.")
        exit(1)

    total_collected = 0
    for subreddit in subreddits:
        for search_term in search_terms:
            posts = fetch_reddit_posts(subreddit, search_term)
            for post in posts:
                insert_post(conn, post)
            total_collected += len(posts)
            print(f"Collected {len(posts)} posts from r/{subreddit} for search term '{search_term}'")
            time.sleep(2)

    print(f"Total posts collected: {total_collected}")
    conn.close() 