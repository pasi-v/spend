SELECT
    SUM(amount_cents)/100 AS total_amount
  , stores.name
FROM vouchers
LEFT JOIN stores USING (store_id)
GROUP BY store_id
ORDER BY total_amount DESC
LIMIT 20;
