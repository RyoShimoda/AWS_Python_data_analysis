WITH category_gmv AS (
    SELECT
        oi.order_id,
        -- product_category_nameがNULLの場合は、'uncategorized'として扱う
        COALESCE(
            NULLIF(TRIM(t.product_category_name_english), ''),
            NULLIF(TRIM(p.product_category_name), ''),
            'uncategorized'
        ) AS product_category,

        SUM(oi.price) AS category_gmv
    FROM order_items AS oi

    LEFT JOIN products AS p
        ON oi.product_id = p.product_id

    LEFT JOIN product_category_name_translation AS t
        ON p.product_category_name = t.product_category_name

    GROUP BY
        oi.order_id,
        COALESCE(
            NULLIF(TRIM(t.product_category_name_english), ''),
            NULLIF(TRIM(p.product_category_name), ''),
            'uncategorized'
        )
),

ranked_category AS (
    SELECT
        order_id,
        product_category,
        category_gmv,
        --注文（order_id）ごとに、category_gmvの降順でランク付けする
        -- 同額の場合、product_categoryの昇順でランク付けする
        ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY
                category_gmv DESC,
                product_category ASC
        ) AS category_rank

    FROM category_gmv
)

SELECT
    order_id,
    product_category AS main_category,
    category_gmv AS main_category_gmv

FROM ranked_category

WHERE category_rank = 1

ORDER BY
    order_id;
