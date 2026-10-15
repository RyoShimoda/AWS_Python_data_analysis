WITH order_gmv AS (
    SELECT
        order_id,
        SUM(price) AS order_gmv
    FROM order_items
    GROUP BY
        order_id
),

customer_orders AS (
    SELECT
        o.order_id,
        c.customer_unique_id,
        CAST(o.order_purchase_timestamp AS TIMESTAMP) AS purchase_timestamp,
        g.order_gmv
    FROM orders AS o

    INNER JOIN customers AS c
        ON o.customer_id = c.customer_id

    INNER JOIN order_gmv AS g
        ON o.order_id = g.order_id

    WHERE
        o.order_purchase_timestamp IS NOT NULL
),

history_base AS (
    SELECT
        order_id,
        customer_unique_id,
        purchase_timestamp,
        order_gmv,

        -- -1を加えることで、その注文より前の購入回数にする（現在の注文を含めない）
        ROW_NUMBER() OVER (
            PARTITION BY customer_unique_id
            ORDER BY
                purchase_timestamp,
                order_id
        ) - 1 AS prior_order_count,

        SUM(order_gmv) OVER (
            PARTITION BY customer_unique_id
            ORDER BY
                purchase_timestamp,
                order_id
            -- 顧客の一番古い注文から「現在の1つ前の注文」までを合計する
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS prior_customer_gmv,

        -- 同じ顧客の1つ前の注文日時を取得する
        LAG(purchase_timestamp) OVER (
            PARTITION BY customer_unique_id
            ORDER BY
                purchase_timestamp,
                order_id
        ) AS previous_purchase_timestamp

    FROM customer_orders
)

SELECT
    order_id,
    customer_unique_id,

    prior_order_count,

    CASE
        WHEN prior_order_count > 0 THEN 1
        ELSE 0
    END AS is_repeat_customer,

    COALESCE(
        prior_customer_gmv,
        0
    ) AS prior_customer_gmv,

    CASE
        WHEN prior_order_count > 0
        THEN prior_customer_gmv / prior_order_count
        ELSE 0
    END AS prior_avg_order_value,

    CASE
        WHEN previous_purchase_timestamp IS NOT NULL
        THEN DATE_DIFF(
            'day',
            previous_purchase_timestamp,
            purchase_timestamp
        )
        ELSE NULL
    END AS days_since_previous_order

FROM history_base

ORDER BY
    order_id;
