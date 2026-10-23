WITH valid_reviews AS (
    SELECT
        order_id,
        TRY_CAST(review_answer_timestamp AS TIMESTAMP)
            AS review_timestamp
    FROM olist.reviews
    WHERE order_id IS NOT NULL
      AND TRIM(order_id) <> ''
      AND review_score IN ('1', '2', '3', '4', '5')
),

review_summary AS (
    SELECT
        order_id,
        COUNT(*) AS review_count,
        COUNT(review_timestamp) AS timestamp_count,
        MIN(review_timestamp) AS first_review_timestamp,
        MAX(review_timestamp) AS last_review_timestamp
    FROM valid_reviews
    GROUP BY order_id
),

order_review_timing AS (
    SELECT
        o.order_id,
        r.review_count,
        r.timestamp_count,
        TRY_CAST(
            o.order_delivered_customer_date AS TIMESTAMP
        ) AS delivered_timestamp,
        r.first_review_timestamp,
        r.last_review_timestamp
    FROM olist.orders o
    JOIN review_summary r
        ON o.order_id = r.order_id
)

SELECT
    order_id,
    review_count,
    timestamp_count,
    review_count - timestamp_count
        AS missing_review_timestamp_count,
    delivered_timestamp,
    first_review_timestamp,
    last_review_timestamp,

    CASE
        WHEN delivered_timestamp IS NULL
            THEN 'delivery_timestamp_missing'
        WHEN timestamp_count < review_count
            THEN 'review_timestamp_missing'
        WHEN last_review_timestamp < delivered_timestamp
            THEN 'all_reviews_before_delivery'
        WHEN first_review_timestamp >= delivered_timestamp
            THEN 'all_reviews_after_delivery'
        ELSE 'reviews_before_and_after_delivery'
    END AS timing_category

FROM order_review_timing
ORDER BY order_id;
