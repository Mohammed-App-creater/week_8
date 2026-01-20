"""
YOLO Image Enrichment Orchestration Module

This module provides a wrapper for the YOLOv8 image enrichment pipeline.
It can be called from orchestration tools like Dagster or run standalone.
"""

import os
import sys
import logging
from pathlib import Path

# Add image_enrichment directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "image_enrichment"))

from infer_images import ImageEnrichmentPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_yolo_enrichment(
    image_dir: str = None,
    output_file: str = None,
    model_name: str = "yolov8n.pt"
):
    """
    Task 3: Enrich data using YOLOv8 for object detection in images.
    
    This function wraps the YOLOv8 enrichment pipeline for use in
    orchestration workflows (Dagster, Airflow, etc.).
    
    Args:
        image_dir: Directory containing images to process
        output_file: Path to output JSON file
        model_name: YOLOv8 model variant to use
    """
    logger.info("=" * 60)
    logger.info("Task 3: YOLO Image Enrichment")
    logger.info("=" * 60)
    
    # Determine project root
    project_root = Path(__file__).parent.parent
    
    # Set defaults if not provided
    if image_dir is None:
        image_dir = str(project_root / "data" / "raw" / "images")
    
    if output_file is None:
        output_file = str(
            project_root / "image_enrichment" / "outputs" / "image_detections.json"
        )
    
    logger.info(f"Images directory: {image_dir}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Model: {model_name}")
    
    # Initialize and run pipeline
    try:
        pipeline = ImageEnrichmentPipeline(
            model_name=model_name,
            images_dir=image_dir,
            output_file=output_file,
            confidence_threshold=0.25
        )
        
        pipeline.run()
        
        logger.info("YOLO enrichment completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"YOLO enrichment failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    # Can be called with custom parameters or defaults
    success = run_yolo_enrichment()
    sys.exit(0 if success else 1)

