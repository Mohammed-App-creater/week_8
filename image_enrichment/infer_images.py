"""
YOLOv8 Image Enrichment Pipeline for Telegram Messages

This module performs object detection on Telegram message images using YOLOv8.
It enriches the ELT pipeline by extracting structured metadata about detected objects,
enabling multimodal analytics that combine text and visual content.

The enriched data supports:
- Product category detection in medical/pharmaceutical images
- Visual content analysis for trend identification
- Multimodal cross-referencing between message text and image content
"""

import json
import csv
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np
from ultralytics import YOLO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_enrichment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ImageEnrichmentPipeline:
    """
    YOLOv8-based image enrichment pipeline for Telegram message images.
    
    This pipeline loads a pretrained YOLOv8 model and performs object detection
    on images scraped from Telegram channels. Results are stored as structured
    JSON records that can be loaded into PostgreSQL for multimodal analytics.
    """
    
    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        images_dir: str = "data/raw/images",
        output_file: str = "image_enrichment/outputs/image_detections.json",
        confidence_threshold: float = 0.25
    ):
        """
        Initialize the image enrichment pipeline.
        
        Args:
            model_name: YOLOv8 model variant (yolov8n, yolov8s, etc.)
            images_dir: Directory containing Telegram message images
            output_file: Path to output JSON file for detection results
            confidence_threshold: Minimum confidence score for detections
        """
        self.model_name = model_name
        self.images_dir = Path(images_dir)
        self.output_file = Path(output_file)
        self.confidence_threshold = confidence_threshold
        
        # Check and log directory structure
        logger.info(f"Images directory: {self.images_dir}")
        logger.info(f"Images directory exists: {self.images_dir.exists()}")
        
        if self.images_dir.exists():
            # List subdirectories
            subdirs = [d for d in self.images_dir.iterdir() if d.is_dir()]
            if subdirs:
                logger.info(f"Found {len(subdirs)} subdirectories:")
                for subdir in subdirs:
                    # Count images in each subdirectory
                    img_count = len([f for f in subdir.iterdir() 
                                   if f.is_file() and f.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}])
                    logger.info(f"  - {subdir.name}: {img_count} images")
            else:
                logger.info("No subdirectories found in images directory")
        
        # Ensure output directory exists
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load YOLOv8 model
        logger.info(f"Loading YOLOv8 model: {model_name}")
        self.model = YOLO(model_name)
        logger.info(f"Model loaded successfully. Classes: {len(self.model.names)}")
        
    def extract_message_id(self, image_filename: str) -> Optional[str]:
        """
        Extract Telegram message_id from image filename.
        
        Expected format: <message_id>_<index>.jpg or <message_id>.jpg
        
        Args:
            image_filename: Name of the image file
            
        Returns:
            Extracted message_id or None if format is invalid
        """
        try:
            # Remove extension
            name_without_ext = Path(image_filename).stem
            
            # Handle format: message_id_index
            if '_' in name_without_ext:
                message_id = name_without_ext.split('_')[0]
            else:
                message_id = name_without_ext
                
            return message_id
        except Exception as e:
            logger.warning(f"Could not extract message_id from {image_filename}: {e}")
            return None
    
    def run_inference(self, image_path: Path) -> Optional[Dict]:
        """
        Run YOLOv8 inference on a single image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Detection results dictionary or None if inference fails
        """
        try:
            # Read image
            img = cv2.imread(str(image_path))
            if img is None:
                logger.error(f"Failed to read image: {image_path}")
                return None
            
            # Run inference
            results = self.model(img, conf=self.confidence_threshold, verbose=False)
            
            if not results or len(results) == 0:
                logger.warning(f"No results returned for {image_path}")
                return None
            
            # Extract detection information
            result = results[0]
            
            detected_objects = []
            confidences = []
            
            # Process each detection
            if result.boxes is not None and len(result.boxes) > 0:
                for box in result.boxes:
                    # Extract class and confidence
                    cls_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    class_name = self.model.names[cls_id]
                    
                    detected_objects.append({
                        "class": class_name,
                        "confidence": round(confidence, 3)
                    })
                    confidences.append(confidence)
            
            # Calculate average confidence
            avg_confidence = round(np.mean(confidences), 3) if confidences else 0.0
            
            return {
                "detected_objects": detected_objects,
                "object_count": len(detected_objects),
                "avg_confidence": avg_confidence
            }
            
        except Exception as e:
            logger.error(f"Inference failed for {image_path}: {e}", exc_info=True)
            return None
    
    def process_all_images(self) -> List[Dict]:
        """
        Process all images in the images directory and its subdirectories.
        
        Returns:
            List of detection records
        """
        if not self.images_dir.exists():
            logger.error(f"Images directory not found: {self.images_dir}")
            return []
        
        # Get all image files recursively from all subdirectories
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        image_files = []
        
        logger.info(f"Searching for images in: {self.images_dir}")
        
        # Recursively find all image files using rglob
        for ext in image_extensions:
            image_files.extend(self.images_dir.rglob(f"*{ext}"))
            image_files.extend(self.images_dir.rglob(f"*{ext.upper()}"))  # uppercase extensions
        
        logger.info(f"Found {len(image_files)} images in total (including subdirectories)")
        
        # Log sample image paths
        if image_files:
            logger.info("Sample image paths (relative to images_dir):")
            for img_path in image_files[:5]:
                rel_path = img_path.relative_to(self.images_dir)
                logger.info(f"  - {rel_path}")
            if len(image_files) > 5:
                logger.info(f"  ... and {len(image_files) - 5} more")
        
        detection_records = []
        processed_count = 0
        error_count = 0
        
        for image_path in image_files:
            # Get relative path for logging
            rel_path = image_path.relative_to(self.images_dir)
            logger.info(f"Processing: {rel_path}")
            
            # Extract message_id from filename
            message_id = self.extract_message_id(image_path.name)
            if message_id is None:
                logger.warning(f"Skipping {rel_path}: Could not extract message_id")
                error_count += 1
                continue
            
            # Run inference
            detection_result = self.run_inference(image_path)
            
            if detection_result is None:
                logger.warning(f"Skipping {rel_path}: Inference failed")
                error_count += 1
                continue
            
            # Create structured record
            record = {
                "message_id": message_id,
                "image_path": str(image_path),
                "relative_path": str(rel_path),
                "subdirectory": str(rel_path.parent),
                "detected_objects": detection_result["detected_objects"],
                "object_count": detection_result["object_count"],
                "avg_confidence": detection_result["avg_confidence"],
                "model_version": self.model_name,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
            detection_records.append(record)
            processed_count += 1
            
            # Log progress every 10 images
            if processed_count % 10 == 0:
                logger.info(f"Progress: {processed_count}/{len(image_files)} images processed")
        
        logger.info(f"Processing complete. Success: {processed_count}, Errors: {error_count}")
        return detection_records
    
    def save_results(self, detection_records: List[Dict]) -> None:
        """
        Save detection results to JSON file.
        
        Args:
            detection_records: List of detection records to save
        """
        try:
            # Write incrementally (append mode)
            # If file exists, read existing records and merge
            existing_records = []
            if self.output_file.exists():
                try:
                    with open(self.output_file, 'r', encoding='utf-8') as f:
                        existing_records = json.load(f)
                    logger.info(f"Loaded {len(existing_records)} existing records")
                except json.JSONDecodeError:
                    logger.warning("Could not parse existing JSON file, will overwrite")
            
            # Merge records (avoid duplicates by message_id and image_path)
            existing_keys = {(r['message_id'], r['image_path']) for r in existing_records}
            new_records = [r for r in detection_records if (r['message_id'], r['image_path']) not in existing_keys]
            
            all_records = existing_records + new_records
            
            # Write to file
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(all_records, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(all_records)} total records to {self.output_file}")
            logger.info(f"New records added: {len(new_records)}")
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}", exc_info=True)
    
    def save_results_csv(self, detection_records: List[Dict]) -> None:
        """
        Save detection results to CSV file in flattened format.
        
        Each detected object becomes one row with:
        - message_id
        - detected_class
        - confidence_score
        
        Args:
            detection_records: List of detection records to save
        """
        try:
            # Generate CSV file path (same directory as JSON output)
            csv_output_file = self.output_file.parent / "image_detections.csv"
            
            # Flatten nested structure: one row per detected object
            flattened_rows = []
            for record in detection_records:
                message_id = record['message_id']
                detected_objects = record.get('detected_objects', [])
                
                if detected_objects:
                    # Create one row for each detected object
                    for obj in detected_objects:
                        flattened_rows.append({
                            'message_id': message_id,
                            'detected_class': obj['class'],
                            'confidence_score': obj['confidence']
                        })
                # Note: Messages with no detections won't appear in CSV
                # This is intentional - we only load detected objects
            
            # Write to CSV
            if flattened_rows:
                with open(csv_output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['message_id', 'detected_class', 'confidence_score'])
                    writer.writeheader()
                    writer.writerows(flattened_rows)
                
                logger.info(f"Saved {len(flattened_rows)} detection rows to {csv_output_file}")
            else:
                logger.warning("No detections to save to CSV")
                
        except Exception as e:
            logger.error(f"Failed to save CSV results: {e}", exc_info=True)
    
    def run(self) -> None:
        """
        Execute the complete image enrichment pipeline.
        """
        logger.info("=" * 60)
        logger.info("Starting YOLOv8 Image Enrichment Pipeline")
        logger.info("=" * 60)
        
        # Process all images
        detection_records = self.process_all_images()
        
        # Save results
        if detection_records:
            self.save_results(detection_records)
            self.save_results_csv(detection_records)
        else:
            logger.warning("No detection records to save")
        
        logger.info("=" * 60)
        logger.info("Pipeline execution complete")
        logger.info("=" * 60)


def main():
    """
    Main entry point for the image enrichment pipeline.
    
    This script can be run standalone or imported as a module.
    Configuration can be adjusted via environment variables or command-line args.
    """
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    # Configuration (can be overridden via environment variables)
    model_name = os.getenv("YOLO_MODEL", "yolov8n.pt")
    
    # Default paths relative to project root
    default_images_dir = project_root / "data" / "raw" / "images"
    default_output_file = project_root / "image_enrichment" / "outputs" / "image_detections.json"
    
    # Get environment variables or use defaults
    images_dir_env = os.getenv("IMAGES_DIR")
    output_file_env = os.getenv("OUTPUT_FILE")
    
    # Resolve images directory
    if images_dir_env:
        # If env var provided, resolve it
        images_dir = Path(images_dir_env).resolve()
    else:
        # Use default
        images_dir = default_images_dir
    
    # Resolve output file
    if output_file_env:
        # If env var is absolute path
        if Path(output_file_env).is_absolute():
            output_file = Path(output_file_env)
        else:
            # If relative, resolve relative to project root
            output_file = project_root / output_file_env
    else:
        # Use default
        output_file = default_output_file
    
    confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))
    
    # Log the paths for debugging
    logger.info(f"Project root: {project_root}")
    logger.info(f"Images directory: {images_dir}")
    logger.info(f"Images directory exists: {images_dir.exists()}")
    logger.info(f"Output file: {output_file}")
    
    # Initialize and run pipeline
    pipeline = ImageEnrichmentPipeline(
        model_name=model_name,
        images_dir=str(images_dir),  # Convert to string for compatibility
        output_file=str(output_file),
        confidence_threshold=confidence_threshold
    )
    
    pipeline.run()


if __name__ == "__main__":
    main()