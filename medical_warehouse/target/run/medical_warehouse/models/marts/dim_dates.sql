
  
    

  create  table "medical_warehouse"."analytics"."dim_dates__dbt_tmp"
  
  
    as
  
  (
    /*
    Mart Model: dim_dates
    Purpose: Date dimension table to support time-based analysis.
    Grain: One row per day.
*/

with stg_dates as (
    select distinct 
        date(message_date) as full_date
    from "medical_warehouse"."analytics"."stg_telegram_messages"
    where message_date is not null
),

date_details as (
    select
        full_date,
        cast(to_char(full_date, 'YYYYMMDD') as int) as date_key,
        extract(dow from full_date) as day_of_week,
        to_char(full_date, 'Day') as day_name,
        extract(week from full_date) as week_of_year,
        extract(month from full_date) as month,
        to_char(full_date, 'Month') as month_name,
        extract(quarter from full_date) as quarter,
        extract(year from full_date) as year
    from stg_dates
)

select
    date_key,
    full_date,
    day_of_week,
    day_name,
    week_of_year,
    month,
    month_name,
    quarter,
    year,
    case 
        when day_of_week in (0, 6) then true -- 0 is Sunday, 6 is Saturday in Postgres (usually, check specific DB settings)
        else false 
    end as is_weekend
from date_details
  );
  