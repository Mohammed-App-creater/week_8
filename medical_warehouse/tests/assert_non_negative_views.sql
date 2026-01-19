-- Custom test: assert_non_negative_views
-- Returns rows where view count is less than 0, which should be impossible.

select *
from {{ ref('stg_telegram_messages') }}
where views < 0
