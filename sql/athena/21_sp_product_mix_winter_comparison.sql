-- SPの2017年冬・2018年冬について、カテゴリ内の商品構成を比較する。
-- 先に確認した4カテゴリに絞る。GMVは商品価格で、送料は含めない。
-- 1行は「季節×カテゴリ×商品ID」。顧客・注文IDは出力しない。

WITH sp_delivered_orders AS (
    SELECT
        o.order_id,
        CASE
            WHEN SUBSTR(o.order_purchase_timestamp, 1, 7)
                BETWEEN '2017-06' AND '2017-08' THEN '2017 Winter'
            WHEN SUBSTR(o.order_purchase_timestamp, 1, 7)
                BETWEEN '2018-06' AND '2018-08' THEN '2018 Winter'
        END AS season_label
    FROM orders o
    JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
      AND c.customer_state = 'SP'
      AND o.order_id IS NOT NULL
      AND TRIM(o.order_id) <> ''
      AND o.order_purchase_timestamp IS NOT NULL
      AND TRIM(o.order_purchase_timestamp) <> ''
      AND (
          SUBSTR(o.order_purchase_timestamp, 1, 7)
              BETWEEN '2017-06' AND '2017-08'
          OR SUBSTR(o.order_purchase_timestamp, 1, 7)
              BETWEEN '2018-06' AND '2018-08'
      )
),

product_items AS (
    SELECT
        d.season_label,
        COALESCE(
            NULLIF(TRIM(t.product_category_name_english), ''),
            NULLIF(TRIM(p.product_category_name), ''),
            'uncategorized'
        ) AS product_category,
        oi.product_id,
        oi.order_id,
        oi.price
    FROM sp_delivered_orders d
    JOIN order_items oi
        ON d.order_id = oi.order_id
    LEFT JOIN products p
        ON oi.product_id = p.product_id
    LEFT JOIN product_category_name_translation t
        ON p.product_category_name = t.product_category_name
)

SELECT
    season_label,
    product_category,
    product_id,
    COUNT(DISTINCT order_id) AS product_order_count,
    COUNT(*) AS item_line_count,
    SUM(price) AS product_gmv
FROM product_items
WHERE product_category IN (
    'bed_bath_table',
    'health_beauty',
    'watches_gifts',
    'computers_accessories'
)
GROUP BY season_label, product_category, product_id
ORDER BY season_label, product_category, product_gmv DESC;
