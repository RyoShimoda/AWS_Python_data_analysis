select
    oi.order_id,
    COUNT(*) AS item_count,
    COUNT(DISTINCT COALESCE(
        p.product_category_name,
        'uncategorized'
    )) AS category_count

from order_items oi
left join products p
    on oi.product_id = p.product_id
group by oi.order_id
order by oi.order_id;
