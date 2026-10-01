-- SP・PB・APの購入月×顧客州×商品カテゴリ別に注文数とGMVを集計する。
-- 売上基準分析と同じ配達済み注文を対象にし、GMVに送料を含めない。
-- 月は配送日ではなく購入日で決める。季節への集約はNotebookで行う。

WITH order_item_summary AS (
    -- 注文全体のGMV。カテゴリを含む注文の「注文全体の平均額」を後で求めるために使う。
    SELECT
        order_id,
        SUM(price) AS order_gmv
    FROM order_items
    WHERE order_id IS NOT NULL
      AND TRIM(order_id) <> ''
    GROUP BY order_id
),

delivered_orders AS (
    SELECT
        DATE_FORMAT(
            CAST(
                DATE_TRUNC(
                    'month',
                    CAST(CAST(SUBSTR(o.order_purchase_timestamp, 1, 10) AS date) AS timestamp)
                ) AS timestamp
            ),
            '%Y-%m'
        ) AS purchase_month,
        c.customer_state,
        o.order_id
    FROM orders o
    JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_id IS NOT NULL
      AND TRIM(o.order_id) <> ''
      AND o.order_purchase_timestamp IS NOT NULL
      AND TRIM(o.order_purchase_timestamp) <> ''
      AND c.customer_state IN ('SP', 'PB', 'AP')
),

order_category AS (
    -- 同じ注文に同じカテゴリの商品が複数あっても、注文×カテゴリを1行にする。
    SELECT
        d.purchase_month,
        d.customer_state,
        oi.order_id,
        COALESCE(
            NULLIF(TRIM(t.product_category_name_english), ''),
            NULLIF(TRIM(p.product_category_name), ''),
            'uncategorized'
        ) AS product_category,
        SUM(oi.price) AS order_category_gmv
    FROM delivered_orders d
    JOIN order_items oi
        ON d.order_id = oi.order_id
    LEFT JOIN products p
        ON oi.product_id = p.product_id
    LEFT JOIN product_category_name_translation t
        ON p.product_category_name = t.product_category_name
    GROUP BY
        d.purchase_month,
        d.customer_state,
        oi.order_id,
        COALESCE(
            NULLIF(TRIM(t.product_category_name_english), ''),
            NULLIF(TRIM(p.product_category_name), ''),
            'uncategorized'
        )
)

SELECT
    oc.purchase_month,
    oc.customer_state,
    oc.product_category,
    COUNT(*) AS category_order_count,
    SUM(oc.order_category_gmv) AS category_gmv,
    SUM(i.order_gmv) AS category_order_total_gmv
FROM order_category oc
JOIN order_item_summary i
    ON oc.order_id = i.order_id
GROUP BY
    oc.purchase_month,
    oc.customer_state,
    oc.product_category
ORDER BY
    oc.purchase_month,
    oc.customer_state,
    category_gmv DESC;
