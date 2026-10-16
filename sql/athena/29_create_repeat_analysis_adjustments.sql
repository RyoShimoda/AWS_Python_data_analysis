WITH order_gmv AS (
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
        o.order_status,

        TRY_CAST(
            o.order_purchase_timestamp AS TIMESTAMP
        ) AS purchase_timestamp,

        g.order_gmv,

        CASE
            WHEN g.order_id IS NULL THEN 0
            ELSE 1
        END AS has_order_items

    FROM orders o

    INNER JOIN customers c
        ON o.customer_id = c.customer_id

    LEFT JOIN order_gmv g
        ON o.order_id = g.order_id
),

customer_history AS (
    SELECT
        order_id,
        customer_unique_id,
        order_status,
        purchase_timestamp,
        order_gmv,
        has_order_items,

        ROW_NUMBER() OVER (
            PARTITION BY customer_unique_id
            ORDER BY purchase_timestamp, order_id
        ) - 1 AS prior_order_count

    FROM customer_orders

    WHERE purchase_timestamp IS NOT NULL
)

SELECT
    order_id,
    customer_unique_id,
    order_status,
    purchase_timestamp,
    order_gmv,
    has_order_items,
    prior_order_count

FROM customer_history

ORDER BY order_id;
