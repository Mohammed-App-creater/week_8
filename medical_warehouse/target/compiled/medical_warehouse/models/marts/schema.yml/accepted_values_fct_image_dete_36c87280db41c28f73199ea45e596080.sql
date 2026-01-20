
    
    

with all_values as (

    select
        image_category as value_field,
        count(*) as n_records

    from "medical_warehouse"."analytics"."fct_image_detections"
    group by image_category

)

select *
from all_values
where value_field not in (
    'promotional','product_display','other'
)


