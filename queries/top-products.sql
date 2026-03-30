SELECT
    SUM(amount_cents)/100 AS total_amount
  , products.name
FROM vouchers
LEFT JOIN products USING (product_id)
GROUP BY product_id
ORDER BY total_amount DESC
LIMIT 20;
