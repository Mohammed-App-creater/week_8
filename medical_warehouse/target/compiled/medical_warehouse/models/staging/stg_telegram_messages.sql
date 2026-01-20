/*
    Staging Model: stg_telegram_messages
    Purpose: Cleans and standardizes raw telegram message data.
    Grain: One row per message.
*/

with source as (
    select * from "medical_warehouse"."raw"."telegram_messages"
),

renamed as (
    select
        -- IDs
        id as message_id,
        
        -- Dimensions
        channel_name,
        message_text,
        image_path,
        
        -- Timestamps
        message_date::timestamp AT TIME ZONE 'UTC' as message_date,
        
        -- Metrics
        views::int as views,
        forwards::int as forwards,

        -- Preserve raw payload
        to_jsonb(source) as raw_payload

    from source
)

select
    message_id,
    channel_name,
    message_date,
    message_text,
    views,
    forwards,
    image_path,

    -- Derived columns
    length(message_text) as message_length,
    case 
        when image_path is not null then true 
        else false 
    end as has_image,

    raw_payload

from renamed


where message_text is not null and message_text != ''
