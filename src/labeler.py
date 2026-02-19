# 1. Import
import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv
import requests

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

LABELING_PROMPT = """
You are a health misinformation classifier. Your job is to classify Reddit posts about nutrition and supplements into one of four categories.

LABELS:
- misinfo: The post makes factual health claims that are false, unsupported by scientific evidence, or dangerously misleading. Examples: "apple cider vinegar cures cancer", "detoxes flush toxins from your liver"
- accurate: The post makes health claims that are supported by scientific consensus or established medical evidence.
- opinion: The post shares personal experiences, preferences, or asks questions without making factual health claims. Examples: "I feel better after cutting sugar", "has anyone tried this supplement?"
- unsure: The post is ambiguous, contains a mix of accurate and inaccurate claims, or lacks enough context to classify.

RULES:
- Focus on the factual claims, not the tone
- Personal anecdotes are "opinion" unless they include false factual claims
- Questions asking for advice are "opinion" unless they contain false assumptions
- If a post contains both accurate and inaccurate claims, label as "misinfo"
- Questions that assume false premises count as "misinfo" (e.g., "what's the best detox for toxins?" assumes detoxes work)
- A confidence of 1.0 should be rare — use the full range

Classify the following post. Respond ONLY in this exact format:
LABEL: <label>
CONFIDENCE: <a number between 0.0 and 1.0>
REASONING: <one sentence explanation>

POST:
{post_text}
"""

# 4. Function: call to ollama
def call_ollama(post):
    url = "http://localhost:11434/api/generate"
    response = []
    try:
        response = requests.post(url, json={
            "model": "mistral",
            "prompt": LABELING_PROMPT.format(post_text=post),
            "stream": False
        })
        response.raise_for_status()
        result = response.json()["response"]
        return result
    except Exception as e:
        print(f"Error calling Ollama API: {e}")
        return ""

# 5. Function: parse the response
def parse_response(response):
    try:
        lines = [line.strip() for line in response.splitlines()]
        label_line = next(line for line in lines if line.startswith("LABEL:"))
        confidence_line = next(line for line in lines if line.startswith("CONFIDENCE:"))
        reasoning_line = next(line for line in lines if line.startswith("REASONING:"))

        label = label_line.split("LABEL:")[1].strip()
        confidence = confidence_line.split("CONFIDENCE:")[1].strip()
        reasoning = reasoning_line.split("REASONING:")[1].strip()

        return label, confidence, reasoning
    except Exception as e:
        print(f"Error parsing response: {e}")
        return None, None, None

# 6. Function: save labels to database
def save_labels(conn, post_id, label, confidence, reasoning):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO labels (post_id, label, labeled_type, confidence, reasoning)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (post_id, label, 'llm_mistral', confidence, reasoning))
            conn.commit()
    except Exception as e:
        print(f"Error saving labels to database: {e}")
# Main
if __name__ == "__main__":
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        #cursor.execute("SELECT post_id, title, body FROM posts LIMIT 5")  # Limit to 5 for testing
        cursor.execute("""
            SELECT p.post_id, p.title, p.body FROM posts p
            LEFT JOIN labels l ON p.post_id = l.post_id
            WHERE l.post_id IS NULL
        """)
        posts = cursor.fetchall()

        for i, (post_id, title, body) in enumerate(posts):
            print(f"Labeling post {i+1}/{len(posts)} (post_id: {post_id})...")
            post_text = f"{title}\n\n{body}" if body else title 
            response = call_ollama(post_text)
            label, confidence, reasoning = parse_response(response)
            if label and confidence and reasoning:
                save_labels(conn, post_id, label, confidence, reasoning)

        cursor.close()
        conn.close()