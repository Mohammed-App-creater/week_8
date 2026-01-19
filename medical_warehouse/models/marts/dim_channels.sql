
with messages as (
    select * from {{ ref('stg_telegram_messages') }}
),

channel_stats as (
    select
        channel_name,
        min(message_date) as first_post_date,
        max(message_date) as last_post_date,
        count(*) as total_posts,
        avg(views) as avg_views
    from messages
    group by 1
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['channel_name']) }} as channel_key,
        channel_name,
        case
            when lower(channel_name) like '%pharma%' then 'pharmaceutical'
            when lower(channel_name) like '%cosmetic%' then 'cosmetics'
            when lower(channel_name) like '%medic%' then 'medical'
            else 'general'
        end as channel_type,
        first_post_date,
        last_post_date,
        total_posts,
        round(avg_views, 2) as avg_views
    from channel_stats
)

select * from final
