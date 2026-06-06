import sqlite3
import requests
import json
import os

# Configuration
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "Master.db")
INGEST_ENDPOINT = "http://localhost:8000/api/v1/ingest"

def migrate_sqlite_to_graph():
    # 1. Connect to the source SQLite database
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"❌ Error: Could not find SQLite database at {SQLITE_DB_PATH}")
        print("Please ensure your 'Master.db' file is placed inside the backend/ folder.")
        return

    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()

    try:
        # Fetching rows from the legal table (adjust table/column names if your schema differs)
        # Assuming columns: section_number, title, description, chapter
        cursor.execute("SELECT section, title, description, chapter FROM legal_sections;")
        rows = cursor.fetchall()
        print(f"📦 Found {len(rows)} legal sections to ingest. Starting migration...")

    except sqlite3.OperationalError as e:
        print(f"❌ Database Schema Error: {e}")
        print("Check if your table name matches 'legal_sections' or modify the SQL query.")
        conn.close()
        return

    # 2. Iterate and send data to the GraphRAG API
    success_count = 0
    for row in rows:
        section, title, description, chapter = row
        
        # Format the text payload for the LLMGraphTransformer to parse
        combined_text = f"Chapter: {chapter}\nSection: {section}\nTitle: {title}\nProvision: {description}"
        
        payload = {
            "text": combined_text,
            "metadata": {
                "section": str(section),
                "chapter": str(chapter),
                "title": title
            }
        }

        try:
            response = requests.post(
                INGEST_ENDPOINT, 
                json=payload, 
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                success_count += 1
                print(f"✅ Successfully ingested Section {section}: {title}")
            else:
                print(f"⚠️ Failed to ingest Section {section}. Server responded with status: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Could not connect to the backend server. Is main.py running?")
            break

    print(f"\n🚀 Migration Completed! Successfully processed {success_count}/{len(rows)} sections into Neo4j.")
    conn.close()

if __name__ == "__main__":
    migrate_sqlite_to_graph()