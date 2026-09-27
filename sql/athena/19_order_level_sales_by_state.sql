-- 州別の注文額の中央値を計算するため、1注文を1行にまとめる。
-- 対象条件とGMVの定義は14_sales_baseline_by_month_state.sqlに合わせる。
-- GMVは商品価格の合計で、送料は含めない。

WITH order_item_summary AS (
    -- 商品明細は1注文に複数行あるため、先に注文単位へ集約する。
    SELECT
        order_id,
        SUM(price) AS order_gmv,
        SUM(freight_value) AS order_freight
    FROM order_items
    WHERE order_id IS NOT NULL
      AND TRIM(order_id) <> ''
    GROUP BY order_id
),

delivered_orders AS (
    SELECT
        order_id,
        customer_id,
        CAST(SUBSTR(order_purchase_timestamp, 1, 10) AS date) AS purchase_date
    FROM orders
    WHERE order_status = 'delivered'
      AND order_id IS NOT NULL
      AND TRIM(order_id) <> ''
      AND order_purchase_timestamp IS NOT NULL
      AND TRIM(order_purchase_timestamp) <> ''
),

order_sales AS (
    SELECT
        DATE_FORMAT(
            CAST(DATE_TRUNC('month', CAST(d.purchase_date AS timestamp)) AS timestamp),
            '%Y-%m'
        ) AS purchase_month,
        c.customer_state,
        d.order_id,
        i.order_gmv,
        i.order_freight
    FROM delivered_orders d
    JOIN order_item_summary i
        ON d.order_id = i.order_id
    JOIN customers c
        ON d.customer_id = c.customer_id
    WHERE c.customer_state IS NOT NULL
      AND TRIM(c.customer_state) <> ''
)

SELECT
    purchase_month,
    customer_state,
    order_id,
    order_gmv,
    order_freight
FROM order_sales
ORDER BY
    purchase_month,
    customer_state,
    order_id;
