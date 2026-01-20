
  
    

  create  table "medical_warehouse"."analytics"."fct_messages__dbt_tmp"
  
  
    as
  
  (
    /*
    Mart Model: fct_messages
    Purpose: Fact table containing message metrics and keys to dimensions.
    Grain: One row per message.
*/

with stg as (
    select * from "medical_warehouse"."analytics"."stg_telegram_messages"
),

dates as (
    select * from "medical_warehouse"."analytics"."dim_dates"
),

channels as (
    select * from "medical_warehouse"."analytics"."dim_channels"
)

select
    stg.message_id,
    
    -- Foreign Keys
    channels.channel_key,
    dates.date_key,
    
    -- Metrics / Facts
    stg.message_text,
    stg.message_length,
    stg.views as view_count,
    stg.forwards as forward_count,
    stg.has_image,
    stg.image_path,
    
    -- Metadata
    stg.message_date as created_at

from stg
left join channels 
    on stg.channel_name = channels.channel_name
left join dates 
    on date(stg.message_date) = dates.full_date
  );
  