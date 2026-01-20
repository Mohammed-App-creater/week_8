from pydantic import BaseModel
from typing import Optional
from datetime import date

class ChannelStats(BaseModel):
    """Schema for top channels analytics."""
    channel_title: str
    total_messages: int
    total_views: int
    avg_views: float

class MessageTrend(BaseModel):
    """Schema for messages over time."""
    date: date
    message_count: int

class ImageEngagement(BaseModel):
    """Schema for image vs non-image engagement comparison."""
    has_image: bool
    avg_views: float
    avg_forwards: float

class DetectedObject(BaseModel):
    """Schema for top detected objects."""
    object_name: str
    object_count: int

class ProductStats(BaseModel):
    """Schema for top products mentioned."""
    product_name: str
    mention_count: int
