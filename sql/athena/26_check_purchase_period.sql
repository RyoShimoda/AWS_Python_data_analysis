SELECT
    MIN(
        TRY_CAST(o.order_purchase_timestamp AS TIMESTAMP)
    ) AS min_purchase_timestamp,

    MAX(
        TRY_CAST(o.order_purchase_timestamp AS TIMESTAMP)
    ) AS max_purchase_timestamp,

    COUNT(DISTINCT o.order_id) AS order_count,

    COUNT(*) AS review_rows,

    COUNT(r.review_answer_timestamp) AS non_null_review_timestamps,

    MIN(
        TRY_CAST(r.review_answer_timestamp AS TIMESTAMP)
    ) AS min_review_timestamp,

    MAX(
        TRY_CAST(r.review_answer_timestamp AS TIMESTAMP)
    ) AS max_review_timestamp,

    COUNT_IF(
        TRY_CAST(r.review_answer_timestamp AS TIMESTAMP) IS NULL
    ) AS invalid_review_timestamps

FROM orders AS o

INNER JOIN reviews AS r
    ON o.order_id = r.order_id

WHERE o.order_purchase_timestamp IS NOT NULL;
