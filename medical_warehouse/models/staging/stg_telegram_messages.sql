
with source as (
    select * from {{ source('telegram', 'telegram_messages') }}
),

renamed as (
    select
        id as raw_id,
        message_id,
        channel_name,
        message_date,
        message_text,
        views,
        forwards,
        has_media,
        image_path,
        loaded_at
    from source
    where message_text is not null and message_text != ''
),

final as (
    select
        *,
        length(message_text) as message_length,
        case 
            when image_path is not null and image_path != '' then true 
            else false 
        end as has_image
    from renamed
)

select * from final
