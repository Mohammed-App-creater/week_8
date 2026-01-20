/*
    Staging Model: stg_image_detections
    Purpose: Cleans and standardizes raw YOLOv8 image detection data.
    Grain: One row per detected object (message_id + detected_class + confidence_score).
*/

with source as (
    select * from "medical_warehouse"."raw"."image_detections"
),

cleaned as (
    select
        -- IDs (normalize join key)
        message_id::int as message_id,
        
        -- Detection attributes
        detected_class::varchar as detected_class,
        confidence_score::numeric as confidence_score,
        
        -- Metadata
        loaded_at::timestamp as loaded_at
    
    from source
    
    -- Filter out invalid records
    where message_id is not null
      and detected_class is not null
      and confidence_score is not null
)

select
    message_id,
    detected_class,
    confidence_score,
    loaded_at,
    
    -- Derived columns for quality filtering
    case
        when confidence_score >= 0.5 then 'high'
        when confidence_score >= 0.3 then 'medium'
        else 'low'
    end as confidence_level

from cleaned