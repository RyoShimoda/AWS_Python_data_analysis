SELECT
    order_id,
    COUNT(*) AS payment_count,
    COUNT(DISTINCT payment_type) AS payment_type_count,
    MAX(payment_installments) AS max_payment_installments,
    MAX_BY(payment_type, payment_value) AS main_payment_type
FROM
    payments
GROUP BY
    order_id
ORDER BY
    order_id;
