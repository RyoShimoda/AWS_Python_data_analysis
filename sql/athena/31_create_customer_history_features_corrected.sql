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
        TRY_CAST(o.order_purchase_timestamp AS TIMESTAMP)
            AS purchase_timestamp,
        g.order_gmv
    FROM orders AS o
    INNER JOIN customers AS c
        ON o.customer_id = c.customer_id
    INNER JOIN order_gmv AS g
        ON o.order_id = g.order_id
    WHERE TRY_CAST(
        o.order_purchase_timestamp AS TIMESTAMP
    ) IS NOT NULL
),

-- 同じ顧客・同じ購入日時の注文をひとまとめにする
timestamp_groups AS (
    SELECT
        customer_unique_id,
        purchase_timestamp,
        COUNT(*) AS group_order_count,
        SUM(order_gmv) AS group_gmv
    FROM customer_orders
    GROUP BY
        customer_unique_id,
        purchase_timestamp
),

-- 現在の購入日時より前のグループだけを集計
history_by_timestamp AS (
    SELECT
        customer_unique_id,
        purchase_timestamp,

        COALESCE(
            SUM(group_order_count) OVER (
                PARTITION BY customer_unique_id
                ORDER BY purchase_timestamp
                ROWS BETWEEN UNBOUNDED PRECEDING
                     AND 1 PRECEDING
            ),
            0
        ) AS prior_order_count,

        COALESCE(
            SUM(group_gmv) OVER (
                PARTITION BY customer_unique_id
                ORDER BY purchase_timestamp
                ROWS BETWEEN UNBOUNDED PRECEDING
                     AND 1 PRECEDING
            ),
            0
        ) AS prior_customer_gmv,

        LAG(purchase_timestamp) OVER (
            PARTITION BY customer_unique_id
            ORDER BY purchase_timestamp
        ) AS previous_purchase_timestamp

    FROM timestamp_groups
)

SELECT
    co.order_id,
    co.customer_unique_id,

    h.prior_order_count,

    CASE
        WHEN h.prior_order_count > 0 THEN 1
        ELSE 0
    END AS is_repeat_customer,

    h.prior_customer_gmv,

    CASE
        WHEN h.prior_order_count > 0
        THEN h.prior_customer_gmv / h.prior_order_count
        ELSE 0
    END AS prior_avg_order_value,

    CASE
        WHEN h.previous_purchase_timestamp IS NOT NULL
        THEN DATE_DIFF(
            'day',
            h.previous_purchase_timestamp,
            co.purchase_timestamp
        )
        ELSE NULL
    END AS days_since_previous_order

FROM customer_orders AS co
INNER JOIN history_by_timestamp AS h
    ON co.customer_unique_id = h.customer_unique_id
   AND co.purchase_timestamp = h.purchase_timestamp

ORDER BY co.order_id;
