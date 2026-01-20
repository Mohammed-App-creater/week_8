# YOLOv8 Image Enrichment Pipeline

## Overview

This module enriches Telegram message data with visual intelligence using YOLOv8 object detection. It processes images scraped from Telegram channels and extracts structured metadata about detected objects, enabling **multimodal analytics** that combine text and visual content.

### Purpose

The image enrichment pipeline supports:
- **Product category detection** in medical/pharmaceutical images
- **Visual content analysis** for identifying trends across channels
- **Multimodal cross-referencing** between message text and image content
- **Enhanced analytics** for business intelligence and compliance

---

## Architecture

### Input
- **Source**: Images stored in `data/raw/images/`
- **Format**: JPEG, PNG, BMP, TIFF
- **Naming convention**: `<message_id>_<index>.jpg` or `<message_id>.jpg`

### Processing
- **Model**: YOLOv8n (nano) or YOLOv8s (small) pretrained on COCO dataset
- **Task**: Object detection with 80 object classes
- **Confidence threshold**: 0.25 (default, configurable)

### Output
- **JSON File**: `outputs/image_detections.json` - Complete detection records with metadata
- **CSV File**: `outputs/image_detections.csv` - Flattened format for PostgreSQL loading
- **Format**: Structured JSON records + CSV (message_id, detected_class, confidence_score)
- **Schema**: See [Output Schema](#output-schema) section

---

## Installation

### 1. Create Virtual Environment (Recommended)

```bash
# Navigate to image_enrichment directory
cd image_enrichment

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: First run will automatically download the YOLOv8 model (~6MB for yolov8n).

### 3. Verify Installation

```bash
python -c "from ultralytics import YOLO; print('YOLOv8 installed successfully')"
```

---

## Usage

### Basic Usage

```bash
# From project root
cd image_enrichment
python infer_images.py
```

The script will:
1. Load the YOLOv8 model
2. Scan `data/raw/images/` for image files
3. Run object detection on each image
4. Save results to `outputs/image_detections.json`

### Configuration via Environment Variables

```bash
# Use a different model variant
export YOLO_MODEL="yolov8s.pt"

# Use a different images directory
export IMAGES_DIR="path/to/your/images"

# Use a different output file
export OUTPUT_FILE="path/to/output.json"

# Adjust confidence threshold
export CONFIDENCE_THRESHOLD="0.35"

python infer_images.py
```

### Incremental Processing

The pipeline supports **incremental runs**:
- Existing results are preserved
- Only new images (by `message_id`) are processed
- Duplicate `message_id` entries are automatically skipped

This makes it safe to re-run after scraping new Telegram messages.

---

## Output Schema

### JSON Structure

Each detection record contains the following fields:

```json
{
  "message_id": "123456",
  "image_path": "data/raw/images/123456_0.jpg",
  "detected_objects": [
    {
      "class": "person",
      "confidence": 0.892
    },
    {
      "class": "bottle",
      "confidence": 0.764
    }
  ],
  "object_count": 2,
  "avg_confidence": 0.828,
  "model_version": "yolov8n.pt",
  "processed_at": "2026-01-20T15:56:43.123456+00:00"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | Telegram message ID (extracted from filename) |
| `image_path` | string | Absolute path to the image file |
| `detected_objects` | array | List of detected objects with class and confidence |
| `object_count` | integer | Total number of detected objects |
| `avg_confidence` | float | Average confidence score across all detections |
| `model_version` | string | YOLOv8 model variant used for inference |
| `processed_at` | string | ISO 8601 UTC timestamp of processing |

### CSV Structure

The CSV output provides a **flattened** format suitable for PostgreSQL bulk loading:

```csv
message_id,detected_class,confidence_score
123456,person,0.892
123456,bottle,0.764
789012,bottle,0.653
```

**Key differences from JSON:**
- One row per detected object (not per message)
- Messages with multiple detections have multiple rows
- Messages with no detections are excluded from CSV
- Simpler schema focused on core detection data

---

## PostgreSQL Integration (Task 3)

### Overview

Task 3 integrates YOLOv8 detections into the data warehouse using a complete ELT pipeline:

1. **Extract**: YOLO inference generates CSV output
2. **Load**: Python script loads CSV into `raw.image_detections`
3. **Transform**: dbt models clean, join, and enrich detection data

### Step 1: Run YOLO Inference

```bash
# Generate both JSON and CSV outputs
python image_enrichment/infer_images.py
```

This creates:
- `outputs/image_detections.json` - Full records with metadata
- `outputs/image_detections.csv` - Flattened for PostgreSQL

### Step 2: Load into PostgreSQL

Set environment variables:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=medical_warehouse
export DB_USER=your_user
export DB_PASSWORD=your_password
```

Run the loader script:

```bash
python image_enrichment/load_detections_to_postgres.py
```

This script:
- Creates `raw` schema if not exists
- Creates `raw.image_detections` table with schema:
  ```sql
  CREATE TABLE raw.image_detections (
      message_id VARCHAR NOT NULL,
      detected_class VARCHAR NOT NULL,
      confidence_score NUMERIC NOT NULL,
      loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (message_id, detected_class, confidence_score)
  );
  ```
- Loads CSV data using efficient batch insert
- Validates data and reports statistics

### Step 3: Run dbt Models

Navigate to the dbt project:

```bash
cd medical_warehouse
```

Run the staging model:

```bash
dbt run --models stg_image_detections
```

Run the mart model:

```bash
dbt run --models fct_image_detections
```

Run tests:

```bash
dbt test --models fct_image_detections
```

### Data Flow

```
images/ → infer_images.py → CSV → load_detections_to_postgres.py → raw.image_detections
                                                                              ↓
                                                                    stg_image_detections (dbt)
                                                                              ↓
                                                                         ← fct_messages
                                                                              ↓
                                                                    fct_image_detections (enriched)
```

### Validation Queries

The `validation_queries.sql` file contains analytical queries to verify Task 3 completeness:

1. **Query 1**: Do promotional posts get more views than product_display posts?
2. **Query 2**: Which channels use the most visual content?
3. **Query 3**: Temporal trends in visual content categories
4. **Query 4**: Top performing posts by image category
5. **Query 5**: Object co-occurrence analysis

Run queries:

```bash
psql -h localhost -U your_user -d medical_warehouse -f image_enrichment/validation_queries.sql
```

### dbt Models

#### Staging Layer

**`stg_image_detections`** - Cleans and types raw detection data:
- Casts data types (VARCHAR, NUMERIC)
- Filters null values
- Adds `confidence_level` derived column (high/medium/low)

#### Mart Layer

**`fct_image_detections`** - Analytics-ready fact table:
- Joins with `fct_messages` on `message_id`
- Includes `channel_key` and `date_key` for dimensional analysis
- Derives `image_category` using business logic:
  - `person` → `promotional`
  - `bottle/pill/syringe/container` → `product_display`
  - Everything else → `other`
- Includes message metrics (`view_count`, `forward_count`) for engagement analysis

### Analytics Examples

**Compare engagement by image category:**

```sql
SELECT
    image_category,
    COUNT(DISTINCT message_id) as message_count,
    AVG(view_count) as avg_views,
    AVG(forward_count) as avg_forwards
FROM fct_image_detections
GROUP BY image_category
ORDER BY avg_views DESC;
```

**Top channels by visual content:**

```sql
SELECT
    dc.channel_name,
    COUNT(DISTINCT fid.message_id) as messages_with_detections,
    COUNT(*) as total_detections
FROM fct_image_detections fid
INNER JOIN dim_channels dc ON fid.channel_key = dc.channel_key
GROUP BY dc.channel_name
ORDER BY total_detections DESC
LIMIT 10;
```

**Promotional vs product posts over time:**

```sql
SELECT
    dd.year,
    dd.month,
    fid.image_category,
    COUNT(DISTINCT fid.message_id) as message_count,
    AVG(fid.view_count) as avg_views
FROM fct_image_detections fid
INNER JOIN dim_dates dd ON fid.date_key = dd.date_key
GROUP BY dd.year, dd.month, fid.image_category
ORDER BY dd.year, dd.month, fid.image_category;
```

---

## Legacy PostgreSQL Approach (JSON-based)

For reference, the old JSON-based approach is documented below:

### JSON Table Schema

```sql
CREATE TABLE image_detections (
    message_id VARCHAR(50) PRIMARY KEY,
    image_path TEXT NOT NULL,
    detected_objects JSONB NOT NULL,
    object_count INTEGER NOT NULL,
    avg_confidence NUMERIC(5, 3),
    model_version VARCHAR(50),
    processed_at TIMESTAMPTZ NOT NULL
);

-- Add indexes for common queries
CREATE INDEX idx_image_detections_object_count ON image_detections(object_count);
CREATE INDEX idx_image_detections_processed_at ON image_detections(processed_at);
CREATE INDEX idx_image_detections_objects ON image_detections USING GIN(detected_objects);
```

### JSON Analytics Queries

**Option A: Using Python (psycopg2)**

```python
import json
import psycopg2
from psycopg2.extras import Json

# Load JSON file
with open('outputs/image_detections.json', 'r') as f:
    detections = json.load(f)

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="medical_warehouse",
    user="your_user",
    password="your_password"
)
cur = conn.cursor()

# Insert records
for record in detections:
    cur.execute("""
        INSERT INTO image_detections 
        (message_id, image_path, detected_objects, object_count, 
         avg_confidence, model_version, processed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (message_id) DO UPDATE SET
            detected_objects = EXCLUDED.detected_objects,
            object_count = EXCLUDED.object_count,
            avg_confidence = EXCLUDED.avg_confidence,
            processed_at = EXCLUDED.processed_at
    """, (
        record['message_id'],
        record['image_path'],
        Json(record['detected_objects']),
        record['object_count'],
        record['avg_confidence'],
        record['model_version'],
        record['processed_at']
    ))

conn.commit()
cur.close()
conn.close()
```

**Option B: Using dbt (Recommended for ELT)**

Create a dbt seed or source:

```yaml
# models/sources.yml
sources:
  - name: raw
    tables:
      - name: image_detections_json
        description: "Raw image detection results from YOLOv8"
```

Then create a staging model:

```sql
-- models/staging/stg_image_detections.sql
WITH source AS (
    SELECT * FROM {{ source('raw', 'image_detections_json') }}
),

parsed AS (
    SELECT
        message_id,
        image_path,
        detected_objects,
        object_count,
        avg_confidence,
        model_version,
        processed_at::TIMESTAMPTZ AS processed_at
    FROM source
)

SELECT * FROM parsed
```

### Analytics Queries

**Query 1: Most common objects detected**

```sql
SELECT 
    obj->>'class' AS object_class,
    COUNT(*) AS detection_count,
    AVG((obj->>'confidence')::NUMERIC) AS avg_confidence
FROM image_detections,
     jsonb_array_elements(detected_objects) AS obj
GROUP BY obj->>'class'
ORDER BY detection_count DESC
LIMIT 10;
```

**Query 2: Messages with specific objects**

```sql
SELECT 
    message_id,
    object_count,
    avg_confidence,
    processed_at
FROM image_detections
WHERE detected_objects @> '[{"class": "bottle"}]'::jsonb
ORDER BY processed_at DESC;
```

**Query 3: Join with Telegram messages**

```sql
SELECT 
    tm.message_id,
    tm.text,
    tm.date,
    id.object_count,
    id.detected_objects
FROM telegram_messages tm
INNER JOIN image_detections id 
    ON tm.message_id = id.message_id
WHERE id.object_count > 0;
```

---

## Error Handling

The pipeline includes robust error handling:

### Graceful Failures
- **Corrupted images**: Logged and skipped
- **Missing images**: Logged and skipped
- **Invalid filenames**: Logged and skipped
- **Inference errors**: Logged with full stack trace

### Logging
- **File**: `image_enrichment.log`
- **Console**: Real-time progress updates
- **Format**: Timestamp, logger name, level, message

### Recovery
- Re-running the script is safe
- Existing results are preserved
- Only new/failed images are reprocessed

---

## Model Variants

YOLOv8 offers multiple model sizes with speed/accuracy trade-offs:

| Model | Size | Speed | mAP | Use Case |
|-------|------|-------|-----|----------|
| YOLOv8n | 6 MB | Fastest | 37.3 | Development, quick testing |
| YOLOv8s | 22 MB | Fast | 44.9 | Production (default) |
| YOLOv8m | 52 MB | Medium | 50.2 | Higher accuracy needed |
| YOLOv8l | 87 MB | Slow | 52.9 | Best accuracy |
| YOLOv8x | 136 MB | Slowest | 53.9 | Maximum accuracy |

**Recommendation**: Use `yolov8n.pt` for development and `yolov8s.pt` for production.

---

## Multimodal Analytics Use Cases

### 1. Product Category Detection
Detect medical products (bottles, syringes, pills) in Telegram images to:
- Classify channel content by product type
- Track product mentions across text and images
- Identify emerging product trends

### 2. Content Moderation
Identify inappropriate or prohibited content in medical channels:
- Detect weapons, tobacco, or unrelated content
- Flag channels for compliance review

### 3. Trend Analysis
Combine object detection with message timestamps:
- Track temporal trends in product imagery
- Correlate image content with message volume spikes

### 4. Cross-Modal Search
Enable search queries like:
- "Find messages with text 'mask' and images containing people"
- "Show channels discussing 'vaccine' with bottle images"

---

## Performance Considerations

### CPU vs GPU
- **CPU**: YOLOv8n processes ~30-50 images/minute
- **GPU**: YOLOv8n processes ~200-500 images/minute

For large-scale processing (>1000 images), GPU acceleration is recommended.

### GPU Setup (Optional)

```bash
# Install PyTorch with CUDA support
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Verify GPU availability
python -c "import torch; print(torch.cuda.is_available())"
```

---

## Troubleshooting

### Issue: "No module named 'ultralytics'"
**Solution**: Ensure you've installed dependencies:
```bash
pip install -r requirements.txt
```

### Issue: "Images directory not found"
**Solution**: Verify `data/raw/images/` exists and contains images:
```bash
ls data/raw/images/
```

### Issue: "No detection records to save"
**Solution**: Check:
1. Images exist in `data/raw/images/`
2. Image filenames follow naming convention
3. Images are readable (not corrupted)
4. Check `image_enrichment.log` for specific errors

### Issue: Low detection confidence
**Solution**: 
- Lower confidence threshold: `export CONFIDENCE_THRESHOLD="0.15"`
- Use larger model: `export YOLO_MODEL="yolov8s.pt"`

---

## Future Enhancements

- [ ] Custom YOLOv8 fine-tuning on medical products
- [ ] Batch processing with multiprocessing
- [ ] Real-time inference via API endpoint
- [ ] Integration with Dagster orchestration
- [ ] Automatic PostgreSQL loading
- [ ] Support for video frame extraction

---

## License

This module uses:
- **YOLOv8**: AGPL-3.0 (Ultralytics)
- **PyTorch**: BSD-style license
- **OpenCV**: Apache 2.0

---

## Contact

For questions or issues, please refer to the main project README or open an issue in the repository.
