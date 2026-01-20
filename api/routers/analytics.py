from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from api.database import get_db
from api.schemas.analytics import ChannelStats, MessageTrend, ImageEngagement, DetectedObject

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

@router.get("/top-channels", response_model=List[ChannelStats])
def get_top_channels(db: Session = Depends(get_db)):
    """
    Returns top channels by message volume, including view stats.
    """
    query = text("""
        SELECT 
            dc.channel_name AS channel_title,
            COUNT(fm.message_id) AS total_messages,
            COALESCE(SUM(fm.view_count), 0) AS total_views,
            COALESCE(AVG(fm.view_count), 0) AS avg_views
        FROM analytics.fct_messages fm
        JOIN analytics.dim_channels dc ON fm.channel_key = dc.channel_key
        GROUP BY dc.channel_name
        ORDER BY total_messages DESC
        LIMIT 20;
    """)
    result = db.execute(query).mappings().all()
    return result

@router.get("/messages-over-time", response_model=List[MessageTrend])
def get_messages_over_time(db: Session = Depends(get_db)):
    """
    Returns daily message counts.
    """
    query = text("""
        SELECT 
            TO_DATE(fm.date_key::text, 'YYYYMMDD') AS date,
            COUNT(fm.message_id) AS message_count
        FROM analytics.fct_messages fm
        WHERE fm.date_key IS NOT NULL
        GROUP BY TO_DATE(fm.date_key::text, 'YYYYMMDD')
        ORDER BY date DESC
        LIMIT 90;
    """)
    result = db.execute(query).mappings().all()
    return result

@router.get("/image-engagement", response_model=List[ImageEngagement])
def get_image_engagement(db: Session = Depends(get_db)):
    """
    Compares average views and forwards for image vs non-image posts.
    """
    query = text("""
        SELECT 
            CASE WHEN fm.has_image THEN true ELSE false END AS has_image,
            COALESCE(AVG(fm.view_count), 0) AS avg_views,
            COALESCE(AVG(fm.forward_count), 0) AS avg_forwards
        FROM analytics.fct_messages fm
        GROUP BY has_image;
    """)
    result = db.execute(query).mappings().all()
    return result

@router.get("/top-detected-objects", response_model=List[DetectedObject])
def get_top_detected_objects(db: Session = Depends(get_db)):
    """
    Aggregates detected objects from image enrichment table.
    """
    query = text("""
        SELECT 
            fid.detected_class AS object_name,
            COUNT(*) AS object_count
        FROM analytics.fct_image_detections fid
        GROUP BY fid.detected_class
        ORDER BY object_count DESC
        LIMIT 20;
    """)
    result = db.execute(query).mappings().all()
    return result
