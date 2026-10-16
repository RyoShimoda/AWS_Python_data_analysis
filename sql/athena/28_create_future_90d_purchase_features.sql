WITH review_anchor AS (
    SELECT
        order_id,
        review_score,
        review_timestamp,
        low_review
    FROM (
        SELECT
            order_id,
            review_id,
            TRY_CAST(review_score AS INTEGER) AS review_score,
            TRY_CAST(review_answer_timestamp AS TIMESTAMP) AS review_timestamp,

            CASE
                WHEN TRY_CAST(review_score AS INTEGER) <= 2 THEN 1
                ELSE 0
            END AS low_review,

            ROW_NUMBER() OVER (
                PARTITION BY order_id
                ORDER BY
                    TRY_CAST(review_answer_timestamp AS TIMESTAMP),
                    review_id
            ) AS review_rank

        FROM reviews

        WHERE TRY_CAST(review_answer_timestamp AS TIMESTAMP) IS NOT NULL
          AND TRY_CAST(review_score AS INTEGER) BETWEEN 1 AND 5
    ) r
    WHERE review_rank = 1
),

order_gmv AS (
    SELECT
        order_id,
        SUM(price) AS order_gmv
    FROM order_items
    GROUP BY order_id
),

customer_orders AS (
    SELECT
        o.order_id,
        c.customer_unique_id,
        TRY_CAST(o.order_purchase_timestamp AS TIMESTAMP)
            AS purchase_timestamp,
        COALESCE(g.order_gmv, 0) AS order_gmv
    FROM orders o

    INNER JOIN customers c
        ON o.customer_id = c.customer_id

    LEFT JOIN order_gmv g
        ON o.order_id = g.order_id

    WHERE TRY_CAST(o.order_purchase_timestamp AS TIMESTAMP) IS NOT NULL
),

anchor_orders AS (
    SELECT
        r.order_id,
        c.customer_unique_id,
        r.review_score,
        r.low_review,
        r.review_timestamp
    FROM review_anchor r

    INNER JOIN customer_orders c
        ON r.order_id = c.order_id

    -- 2018年8月末まで90日間追跡できるレビューだけを対象にする
    WHERE r.review_timestamp <= TIMESTAMP '2018-06-02 23:59:59'
),

future_purchase_summary AS (
    SELECT
        a.order_id,

        COUNT(f.order_id) AS future_90d_order_count,

        COALESCE(
            SUM(f.order_gmv),
            0
        ) AS future_90d_gmv

    FROM anchor_orders a

    LEFT JOIN customer_orders f
        ON a.customer_unique_id = f.customer_unique_id
       AND a.order_id <> f.order_id
       AND f.purchase_timestamp > a.review_timestamp
       AND f.purchase_timestamp <=
           DATE_ADD('day', 90, a.review_timestamp)

    GROUP BY a.order_id
)

SELECT
    a.order_id,
    a.review_score,
    a.low_review,
    a.review_timestamp,

    CASE
        WHEN s.future_90d_order_count > 0 THEN 1
        ELSE 0
    END AS future_90d_repeat,

    s.future_90d_order_count,
    s.future_90d_gmv

FROM anchor_orders a

INNER JOIN future_purchase_summary s
    ON a.order_id = s.order_id

ORDER BY a.order_id;
