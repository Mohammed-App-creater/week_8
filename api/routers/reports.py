from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from api.database import get_db
from api.schemas.analytics import ProductStats

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

@router.get("/top-products", response_model=List[ProductStats])
def get_top_products(limit: int = 10, db: Session = Depends(get_db)):
    """
    Returns top mentioned products across all channels, combining text and image detections.
    
    Combines:
    - Text search for product keywords in messages
    - Image detections mapped to product categories
    """
    # Hardcoded list of products/keywords to search for, based on business requirements
    # and available detection classes.
    keywords = ['paracetamol', 'vaccine', 'syringe', 'pill', 'bottle', 'container', 'medicine', 'kit']
    
    # Construct dynamic SQL for text search
    # Select 'keyword' as product_name, count(*) from fct_messages where text ilike %keyword%
    text_queries = []
    for k in keywords:
        # Use simple string formatting for the query construction as the keyword is from our trusted list
        # In production, bind parameters should be used for the keyword literal if it came from user input,
        # but here it is a constant list.
        text_queries.append(f"SELECT '{k}' AS product_name, COUNT(*) AS cnt FROM analytics.fct_messages WHERE message_text ILIKE '%{k}%'")
    
    text_union_query = " UNION ALL ".join(text_queries)
    
    # Image detections query
    # We map detected_class to product_name.
    # We filter by the same list of relevant keywords if applicable, or take all as "products" if they match?
    # For now, we assume if the detected class IS one of our keywords, it counts.
    # We also format the list for IN clause.
    quoted_keywords = ", ".join([f"'{k}'" for k in keywords])
    
    image_query = f"""
        SELECT detected_class AS product_name, COUNT(*) AS cnt 
        FROM analytics.fct_image_detections 
        WHERE detected_class IN ({quoted_keywords})
        GROUP BY detected_class
    """
    
    # Final combined query
    full_query = f"""
        WITH text_counts AS (
            {text_union_query}
        ),
        image_counts AS (
            {image_query}
        ),
        combined AS (
            SELECT * FROM text_counts
            UNION ALL
            SELECT * FROM image_counts
        )
        SELECT 
            product_name, 
            SUM(cnt) AS mention_count 
        FROM combined 
        GROUP BY product_name 
        HAVING SUM(cnt) > 0
        ORDER BY mention_count DESC 
        LIMIT :limit;
    """
    
    try:
        result = db.execute(text(full_query), {"limit": limit}).mappings().all()
        return result
    except Exception as e:
        # In a real app we might log this error
        raise HTTPException(status_code=500, detail=str(e))
