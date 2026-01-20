"""
Load YOLOv8 image detection results from CSV into PostgreSQL

This script reads the image_detections.csv file and loads the data
into the raw.image_detections table in PostgreSQL.

Usage:
    python load_detections_to_postgres.py

Environment Variables:
    DB_HOST - PostgreSQL host (default: localhost)
    DB_PORT - PostgreSQL port (default: 5432)
    DB_NAME - Database name (default: medical_warehouse)
    DB_USER - Database user
    DB_PASSWORD - Database password
"""

import csv
import logging
import os
from pathlib import Path
from typing import List, Tuple

import psycopg2
from psycopg2 import OperationalError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImageDetectionLoader:
    """
    Loads YOLOv8 image detection results from CSV into PostgreSQL raw schema.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "medical_warehouse",
        user: str = None,
        password: str = None
    ):
        """
        Initialize the loader with database connection parameters.
        
        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name
            user: Database user
            password: Database password
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
        self.cursor = None
    
    def connect(self) -> None:
        """
        Establish connection to PostgreSQL database.
        """
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to PostgreSQL: {self.database}@{self.host}")
        except OperationalError as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def close(self) -> None:
        """
        Close database connection.
        """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")
    
    def create_raw_schema(self) -> None:
        """
        Create raw schema if it doesn't exist.
        """
        try:
            self.cursor.execute("CREATE SCHEMA IF NOT EXISTS raw")
            self.conn.commit()
            logger.info("Raw schema ensured")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to create raw schema: {e}")
            raise
    
    def create_table(self) -> None:
        """
        Create raw.image_detections table if it doesn't exist.
        """
        create_table_query = """
        CREATE TABLE IF NOT EXISTS raw.image_detections (
            message_id VARCHAR NOT NULL,
            detected_class VARCHAR NOT NULL,
            confidence_score NUMERIC NOT NULL,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (message_id, detected_class, confidence_score)
        );
        
        CREATE INDEX IF NOT EXISTS idx_image_detections_message_id 
        ON raw.image_detections(message_id);
        
        CREATE INDEX IF NOT EXISTS idx_image_detections_class 
        ON raw.image_detections(detected_class);
        """
        
        try:
            self.cursor.execute(create_table_query)
            self.conn.commit()
            logger.info("Table raw.image_detections created/verified")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to create table: {e}")
            raise
    
    def load_csv_file(self, csv_path: Path) -> List[Tuple[str, str, float]]:
        """
        Load detection records from CSV file.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            List of tuples (message_id, detected_class, confidence_score)
        """
        try:
            records = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append((
                        row['message_id'],
                        row['detected_class'],
                        float(row['confidence_score'])
                    ))
            logger.info(f"Loaded {len(records)} detection records from {csv_path}")
            return records
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse CSV: {e}")
            raise
    
    def truncate_table(self) -> None:
        """
        Truncate raw.image_detections table for fresh load.
        """
        try:
            self.cursor.execute("TRUNCATE TABLE raw.image_detections")
            self.conn.commit()
            logger.info("Table raw.image_detections truncated")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to truncate table: {e}")
            raise
    
    def insert_records(self, records: List[Tuple[str, str, float]]) -> None:
        """
        Insert detection records into PostgreSQL using batch insert.
        
        Args:
            records: List of tuples (message_id, detected_class, confidence_score)
        """
        if not records:
            logger.warning("No records to insert")
            return
        
        # SQL query with INSERT
        query = """
            INSERT INTO raw.image_detections (message_id, detected_class, confidence_score)
            VALUES (%s, %s, %s)
            ON CONFLICT (message_id, detected_class, confidence_score) 
            DO NOTHING
        """
        
        try:
            # Execute batch insert
            self.cursor.executemany(query, records)
            self.conn.commit()
            logger.info(f"Successfully inserted {len(records)} records")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to insert records: {e}")
            raise
    
    def verify_load(self) -> dict:
        """
        Verify data was loaded correctly.
        
        Returns:
            Dictionary with verification stats
        """
        try:
            # Count total records
            self.cursor.execute("SELECT COUNT(*) FROM raw.image_detections")
            total_count = self.cursor.fetchone()[0]
            
            # Count unique messages
            self.cursor.execute("""
                SELECT COUNT(DISTINCT message_id) 
                FROM raw.image_detections
            """)
            unique_messages = self.cursor.fetchone()[0]
            
            # Top detected classes
            self.cursor.execute("""
                SELECT detected_class, COUNT(*) as count
                FROM raw.image_detections
                GROUP BY detected_class
                ORDER BY count DESC
                LIMIT 5
            """)
            top_classes = dict(self.cursor.fetchall())
            
            # Average confidence
            self.cursor.execute("""
                SELECT AVG(confidence_score)::NUMERIC(10,3)
                FROM raw.image_detections
            """)
            avg_confidence = self.cursor.fetchone()[0]
            
            stats = {
                'total_detections': total_count,
                'unique_messages': unique_messages,
                'top_classes': top_classes,
                'avg_confidence': float(avg_confidence) if avg_confidence else 0
            }
            
            logger.info("Verification complete:")
            logger.info(f"  Total detections: {stats['total_detections']}")
            logger.info(f"  Unique messages with detections: {stats['unique_messages']}")
            logger.info(f"  Top detected classes: {stats['top_classes']}")
            logger.info(f"  Average confidence: {stats['avg_confidence']}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            raise
    
    def run(self, csv_path: Path, truncate: bool = True) -> None:
        """
        Execute the complete loading pipeline.
        
        Args:
            csv_path: Path to CSV file with detection results
            truncate: Whether to truncate table before loading (default: True)
        """
        logger.info("=" * 60)
        logger.info("Starting Image Detection CSV Loading Pipeline")
        logger.info("=" * 60)
        
        try:
            # Connect to database
            self.connect()
            
            # Create schema and table
            self.create_raw_schema()
            self.create_table()
            
            # Optionally truncate for fresh load
            if truncate:
                self.truncate_table()
            
            # Load CSV data
            records = self.load_csv_file(csv_path)
            
            # Insert records
            self.insert_records(records)
            
            # Verify load
            self.verify_load()
            
            logger.info("=" * 60)
            logger.info("Loading pipeline complete")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise
        finally:
            # Always close connection
            self.close()


def main():
    """
    Main entry point for the loading script.
    """
    # Get database credentials from environment variables
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5432"))
    db_name = os.getenv("DB_NAME", "medical_warehouse")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    
    if not db_user or not db_password:
        logger.error("DB_USER and DB_PASSWORD environment variables must be set")
        logger.info("Example:")
        logger.info("  export DB_USER=your_user")
        logger.info("  export DB_PASSWORD=your_password")
        return
    
    # Determine project root and CSV file path
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    csv_path = project_root / "image_enrichment" / "outputs" / "image_detections.csv"
    
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        logger.info("Run the inference script first to generate CSV: python image_enrichment/infer_images.py")
        return
    
    # Initialize and run loader
    loader = ImageDetectionLoader(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )
    
    loader.run(csv_path, truncate=True)


if __name__ == "__main__":
    main()
