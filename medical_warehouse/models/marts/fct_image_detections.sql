/*
    Mart Model: fct_image_detections
    Purpose: Fact table for YOLO image detections enriched with message context.
    Grain: One row per detected object (message_id + detected_class + confidence_score).
*/

with detections as (
    select * from {{ ref('stg_image_detections') }}
),

messages as (
    select * from {{ ref('fct_messages') }}
)

select
    -- Primary identifiers
    detections.message_id,
    
    -- Foreign Keys from messages
    messages.channel_key,
    messages.date_key,
    
    -- Detection attributes
    detections.detected_class,
    detections.confidence_score,
    detections.confidence_level,
    
    -- Derived business category
    case
        when detections.detected_class = 'person' then 'promotional'
        when detections.detected_class in ('bottle', 'pill', 'syringe', 'container') then 'product_display'
        else 'other'
    end as image_category,
    
    -- Optional: Include message metrics for contextualized analysis
    messages.view_count,
    messages.forward_count,
    messages.created_at as message_date

from detections
inner join messages
    on detections.message_id = messages.message_id
