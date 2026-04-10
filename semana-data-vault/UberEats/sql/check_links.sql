-- row count and sample
SELECT COUNT(*) FROM public_dv_raw.link_order_user_restaurant_driver;
SELECT * FROM public_dv_raw.link_order_user_restaurant_driver LIMIT 10;

-- null hash keys
SELECT *
FROM public_dv_raw.link_order_user_restaurant_driver
WHERE hash_link_order_user_restaurant_driver IS NULL;

SELECT *
FROM public_dv_raw.link_order_user_restaurant_driver
WHERE hash_hub_order_id IS NULL
   OR hash_hub_cpf IS NULL
   OR hash_hub_cnpj IS NULL
   OR hash_hub_license_number IS NULL;

-- duplicate link hash keys
SELECT hash_link_order_user_restaurant_driver, COUNT(*) AS count
FROM public_dv_raw.link_order_user_restaurant_driver
GROUP BY hash_link_order_user_restaurant_driver
HAVING COUNT(*) > 1;

-- load timestamp checks
SELECT *
FROM public_dv_raw.link_order_user_restaurant_driver
WHERE load_dts IS NULL;

SELECT *
FROM public_dv_raw.link_order_user_restaurant_driver
WHERE load_dts > CURRENT_TIMESTAMP();

SELECT DATE_TRUNC('DAY', load_dts) AS load_day, COUNT(*) AS record_count
FROM public_dv_raw.link_order_user_restaurant_driver
GROUP BY 1
ORDER BY 1 DESC;

-- record source & tenant consistency
SELECT record_source, COUNT(*) AS count
FROM public_dv_raw.link_order_user_restaurant_driver
GROUP BY record_source;

-- distribution of multi_tenant_id
SELECT multi_tenant_id, COUNT(*) AS count
FROM public_dv_raw.link_order_user_restaurant_driver
GROUP BY multi_tenant_id;

-- validate hash composition (link vs. stage)
SELECT (
    SELECT COUNT(*) FROM v_stg_orders
    WHERE order_id IS NOT NULL
     AND cpf IS NOT NULL
     AND cnpj IS NOT NULL
     AND license_number IS NOT NULL
) AS valid_stage_records,
(
SELECT COUNT(*) FROM public_dv_raw.link_order_user_restaurant_driver
) AS link_records;
