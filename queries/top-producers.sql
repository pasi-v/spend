SELECT
    SUM(amount_cents)/100 AS total_amount
  , producers.name
FROM vouchers
LEFT JOIN products USING (product_id)
LEFT JOIN producers USING (producer_id)
GROUP BY producer_id
ORDER BY total_amount DESC
LIMIT 20;
