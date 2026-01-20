/*
    Mart Model: dim_channels
    Purpose: Dimension table for derived channel attributes.
    Grain: One row per channel.
*/

with stg as (
    select * from "medical_warehouse"."analytics"."stg_telegram_messages"
),

channel_stats as (
    select
        channel_name,
        min(message_date) as first_post_date,
        max(message_date) as last_post_date,
        count(*) as total_posts,
        avg(views) as avg_views
    from stg
    group by 1
)

select
    -- Surrogate Key - UPDATED to use generate_surrogate_key
    md5(cast(coalesce(cast(channel_name as TEXT), '') as TEXT)) as channel_key,
    
    channel_name,
    
    -- Assuming title is same as name if not distinct in source, or map from another source if avail. 
    -- Requirement says: "channel_title (use channel_name if none)"
    channel_name as channel_title,
    
    -- Placeholder logic for channel_type
    case 
        when channel_name ilike '%news%' then 'News'
        when channel_name ilike '%chart%' then 'Data'
        else 'General'
    end as channel_type,
    
    first_post_date,
    last_post_date,
    total_posts,
    avg_views

from channel_stats