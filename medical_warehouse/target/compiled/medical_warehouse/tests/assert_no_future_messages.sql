-- Custom test: assert_no_future_messages
-- Returns rows where message_date is in the future relative to the current timestamp.

select *
from "medical_warehouse"."analytics"."stg_telegram_messages"
where message_date > now()