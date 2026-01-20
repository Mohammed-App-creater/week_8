select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select confidence_score
from "medical_warehouse"."analytics"."fct_image_detections"
where confidence_score is null



      
    ) dbt_internal_test