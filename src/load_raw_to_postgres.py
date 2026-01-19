import os
import json
import logging
from typing import List, Dict, Any
import psycopg2
from psycopg2 import sql, extras
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

RAW_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw', 'telegram_messages')

def get_db_connection():
    """Create a database connection."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def create_schema_and_table(conn):
    """Create raw schema and telegram_messages table if they don't exist."""
    commands = [
        "CREATE SCHEMA IF NOT EXISTS raw;",
        """
        CREATE TABLE IF NOT EXISTS raw.telegram_messages (
            id SERIAL PRIMARY KEY,
            message_id INTEGER NOT NULL,
            channel_name VARCHAR(255) NOT NULL,
            message_date TIMESTAMP,
            message_text TEXT,
            views INTEGER,
            forwards INTEGER,
            has_media BOOLEAN,
            image_path TEXT,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_message_per_channel UNIQUE (channel_name, message_id)
        );
        """
    ]
    
    try:
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
        conn.commit()
        cur.close()
        logger.info("Schema and table ensured.")
    except Exception as e:
        logger.error(f"Error creating schema/table: {e}")
        conn.rollback()
        raise

def read_json_files(directory: str) -> List[Dict[str, Any]]:
    """Read all JSON files from the directory and its subdirectories."""
    all_messages = []
    
    if not os.path.exists(directory):
        logger.warning(f"Directory {directory} does not exist.")
        return []

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".json"):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        if isinstance(data, list):
                            all_messages.extend(data)
                        elif isinstance(data, dict):
                            all_messages.append(data)
                            
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode JSON: {filepath}")
                except Exception as e:
                    logger.error(f"Error reading file {filepath}: {e}")
                
    logger.info(f"Read {len(all_messages)} messages from JSON files.")
    return all_messages

def load_data_to_postgres(conn, messages: List[Dict[str, Any]]):
    """Load messages into PostgreSQL with upsert (ON CONFLICT DO NOTHING)."""
    if not messages:
        logger.info("No messages to load.")
        return

    query = """
        INSERT INTO raw.telegram_messages (
            message_id, channel_name, message_date, message_text, 
            views, forwards, has_media, image_path
        ) VALUES %s
        ON CONFLICT (channel_name, message_id) DO NOTHING;
    """
    
    # Prepare data tuples
    values = []
    for msg in messages:
        values.append((
            msg.get('message_id'),
            msg.get('channel_name'),
            msg.get('date'),  # Assuming 'date' or 'message_date' in JSON
            msg.get('text') or msg.get('message_text'),
            msg.get('views'),
            msg.get('forwards'),
            msg.get('has_media', False),
            msg.get('image_path')
        ))

    try:
        cur = conn.cursor()
        extras.execute_values(cur, query, values)
        conn.commit()
        cur.close()
        logger.info(f"Successfully processed {len(messages)} records (inserted non-duplicates).")
    except Exception as e:
        logger.error(f"Error loading data to Postgres: {e}")
        conn.rollback()
        raise

def main():
    logger.info("Starting ETL process...")
    
    if not all([DB_NAME, DB_USER, DB_PASSWORD]):
        logger.error("Database credentials missing in environment variables.")
        return

    conn = get_db_connection()
    
    try:
        create_schema_and_table(conn)
        messages = read_json_files(RAW_DATA_PATH)
        if messages:
            # Basic validation/cleaning could go here before loading
            load_data_to_postgres(conn, messages)
    finally:
        conn.close()
        logger.info("ETL process finished.")

if __name__ == "__main__":
    main()
