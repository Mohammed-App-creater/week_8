/*
    Staging Model: stg_telegram_messages
    Purpose: Cleans and standardizes raw telegram message data.
    Grain: One row per message.
*/

with source as (
    select * from {{ source('raw', 'telegram_messages') }}
),

renamed as (
    select
        -- IDs
        id as message_id,
        
        -- Dimensions
        channel_title as channel_name, -- Using channel_title as channel_name per requirements if implies source col
        message as message_text,
        image_path,
        
        -- Timestamps
        date::timestamp AT TIME ZONE 'UTC' as message_date,
        
        -- Metrics
        views::int as views,
        forwards::int as forwards,
        
        -- Logic / Booleans
        media as has_media,
        
        -- Preserve Raw
        -- Assuming the source table structure effectively IS the raw payload, 
        -- we can construct a jsonb object if needed, or pass through a specific column.
        -- If 'raw_telegram_messages' has a json col, use it. 
        -- If not, we can construct one using to_jsonb(source.*) but typically sources have columns.
        -- Requirement: "Preserve original raw payload in a raw_payload column (JSONB) using to_jsonb or the raw column"
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
    has_media,
    
    -- Derived Columns
    length(message_text) as message_length,
    case 
        when has_media = true or image_path is not null then true 
        else false 
    end as has_image,
    
    raw_payload

from renamed

-- Optional filtering using Jinja variable
{% if var('filter_empty_messages', true) %}
where message_text is not null and message_text != ''
{% endif %}
