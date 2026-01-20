-- ============================================================================ 
-- Query 1: Do promotional posts get more views than product_display posts? 
-- ============================================================================
WITH category_metrics AS (
    SELECT
        image_category,
        COUNT(DISTINCT message_id) AS message_count,
        AVG(view_count) AS avg_views,
        AVG(forward_count) AS avg_forwards,
        AVG(confidence_score) AS avg_detection_confidence,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY view_count) AS median_views
    FROM analytics.fct_image_detections
    GROUP BY image_category
)
SELECT
    image_category,
    message_count,
    ROUND(avg_views::numeric, 2) AS avg_views,
    ROUND(median_views::numeric, 2) AS median_views,
    ROUND(avg_forwards::numeric, 2) AS avg_forwards,
    ROUND(avg_detection_confidence::numeric, 3) AS avg_confidence,
    ROUND(100.0 * avg_forwards / NULLIF(avg_views, 0), 2) AS forward_rate_pct
FROM category_metrics
ORDER BY avg_views DESC;


-- ============================================================================ 
-- Query 2: Which channels use the most visual content? 
-- ============================================================================
WITH channel_visual_stats AS (
    SELECT
        dc.channel_name,
        COUNT(DISTINCT fid.message_id) AS messages_with_detections,
        COUNT(*) AS total_detections,
        COUNT(DISTINCT fid.detected_class) AS unique_classes_detected,
        AVG(fid.confidence_score) AS avg_confidence
    FROM analytics.fct_image_detections fid
    INNER JOIN analytics.dim_channels dc ON fid.channel_key = dc.channel_key
    GROUP BY dc.channel_name
),
channel_top_classes AS (
    SELECT
        dc.channel_name,
        fid.detected_class,
        COUNT(*) AS detection_count,
        ROW_NUMBER() OVER (PARTITION BY dc.channel_name ORDER BY COUNT(*) DESC) AS rank
    FROM analytics.fct_image_detections fid
    INNER JOIN analytics.dim_channels dc ON fid.channel_key = dc.channel_key
    GROUP BY dc.channel_name, fid.detected_class
)
SELECT
    cvs.channel_name,
    cvs.messages_with_detections,
    cvs.total_detections,
    ROUND(cvs.total_detections::numeric / NULLIF(cvs.messages_with_detections,0), 2) AS detections_per_message,
    cvs.unique_classes_detected,
    ROUND(cvs.avg_confidence::numeric, 3) AS avg_confidence,
    ctc.detected_class AS most_common_class,
    ctc.detection_count AS most_common_class_count
FROM channel_visual_stats cvs
LEFT JOIN channel_top_classes ctc 
    ON cvs.channel_name = ctc.channel_name AND ctc.rank = 1
ORDER BY cvs.total_detections DESC
LIMIT 10;


-- ============================================================================ 
-- Query 3: Temporal trends in visual content categories 
-- ============================================================================
SELECT
    dd.year,
    dd.month,
    dd.month_name,
    fid.image_category,
    COUNT(DISTINCT fid.message_id) AS message_count,
    ROUND(AVG(fid.view_count)::numeric, 2) AS avg_views,
    ROUND(AVG(fid.confidence_score)::numeric, 3) AS avg_confidence
FROM analytics.fct_image_detections fid
INNER JOIN analytics.dim_dates dd ON fid.date_key = dd.date_key
GROUP BY dd.year, dd.month, dd.month_name, fid.image_category
ORDER BY dd.year DESC, dd.month DESC, fid.image_category;


-- ============================================================================ 
-- Query 4: Top performing posts by image category 
-- ============================================================================
WITH ranked_posts AS (
    SELECT
        fid.message_id,
        dc.channel_name,
        fid.image_category,
        fid.view_count,
        fid.forward_count,
        fid.message_date,
        STRING_AGG(DISTINCT fid.detected_class, ', ') AS detected_objects,
        ROW_NUMBER() OVER (
            PARTITION BY fid.image_category 
            ORDER BY fid.view_count DESC
        ) AS rank_in_category
    FROM analytics.fct_image_detections fid
    INNER JOIN analytics.dim_channels dc ON fid.channel_key = dc.channel_key
    GROUP BY fid.message_id, dc.channel_name, fid.image_category, fid.view_count, fid.forward_count, fid.message_date
)
SELECT
    image_category,
    channel_name,
    message_id,
    view_count,
    forward_count,
    detected_objects,
    message_date::date
FROM ranked_posts
WHERE rank_in_category <= 5
ORDER BY image_category, view_count DESC;


-- ============================================================================ 
-- Query 5: Object co-occurrence analysis 
-- ============================================================================
WITH message_objects AS (
    SELECT
        message_id,
        STRING_AGG(detected_class, ', ' ORDER BY confidence_score DESC) AS object_combination,
        COUNT(DISTINCT detected_class) AS object_count,
        AVG(view_count) AS avg_views
    FROM analytics.fct_image_detections
    GROUP BY message_id
    HAVING COUNT(DISTINCT detected_class) > 1
)
SELECT
    object_combination,
    COUNT(*) AS frequency,
    ROUND(AVG(avg_views)::numeric, 2) AS avg_views_for_combination,
    object_count
FROM message_objects
GROUP BY object_combination, object_count
ORDER BY frequency DESC
LIMIT 20;


-- ============================================================================ 
-- Data Quality Check: Detection Coverage 
-- ============================================================================
SELECT
    total_messages_with_images,
    messages_with_detections,
    ROUND(100.0 * messages_with_detections / NULLIF(total_messages_with_images,0), 2) AS detection_coverage_pct
FROM (
    SELECT
        COUNT(DISTINCT CASE WHEN fm.has_image THEN fm.message_id END) AS total_messages_with_images,
        COUNT(DISTINCT fid.message_id) AS messages_with_detections
    FROM analytics.fct_messages fm
    LEFT JOIN analytics.fct_image_detections fid ON fm.message_id = fid.message_id
) coverage_stats;
