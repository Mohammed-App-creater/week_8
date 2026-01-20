-- Create image_detections table for YOLOv8 object detection results
-- This table stores enriched image data from Telegram messages

CREATE TABLE IF NOT EXISTS image_detections (
    message_id VARCHAR(50) NOT NULL,
    image_path TEXT NOT NULL,
    relative_path TEXT,
    subdirectory TEXT,
    detected_objects JSONB NOT NULL,
    object_count INTEGER NOT NULL CHECK (object_count >= 0),
    avg_confidence NUMERIC(5, 3) CHECK (avg_confidence >= 0 AND avg_confidence <= 1),
    model_version VARCHAR(50),
    processed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Composite primary key (message_id + image_path for multiple images per message)
    PRIMARY KEY (message_id, image_path)
);

-- Add indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_image_detections_message_id 
    ON image_detections(message_id);

CREATE INDEX IF NOT EXISTS idx_image_detections_object_count 
    ON image_detections(object_count);

CREATE INDEX IF NOT EXISTS idx_image_detections_processed_at 
    ON image_detections(processed_at DESC);

CREATE INDEX IF NOT EXISTS idx_image_detections_subdirectory 
    ON image_detections(subdirectory);

-- GIN index for JSONB queries on detected_objects
CREATE INDEX IF NOT EXISTS idx_image_detections_objects_gin 
    ON image_detections USING GIN(detected_objects);

-- Add comments for documentation
COMMENT ON TABLE image_detections IS 
    'YOLOv8 object detection results for Telegram message images. Enables multimodal analytics.';

COMMENT ON COLUMN image_detections.message_id IS 
    'Telegram message ID (foreign key to telegram_messages)';

COMMENT ON COLUMN image_detections.image_path IS 
    'Absolute path to the image file';

COMMENT ON COLUMN image_detections.relative_path IS 
    'Relative path from images directory (for readability)';

COMMENT ON COLUMN image_detections.subdirectory IS 
    'Channel subdirectory name (e.g., lobelia4cosmetics, tikvahpharma)';

COMMENT ON COLUMN image_detections.detected_objects IS 
    'Array of detected objects with class names and confidence scores';

COMMENT ON COLUMN image_detections.object_count IS 
    'Total number of objects detected in the image';

COMMENT ON COLUMN image_detections.avg_confidence IS 
    'Average confidence score across all detections (0-1)';

COMMENT ON COLUMN image_detections.model_version IS 
    'YOLOv8 model variant used (e.g., yolov8n.pt, yolov8s.pt)';

COMMENT ON COLUMN image_detections.processed_at IS 
    'UTC timestamp when the image was processed by YOLOv8';
