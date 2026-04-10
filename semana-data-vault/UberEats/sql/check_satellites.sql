-- row count
SELECT COUNT(*) AS total_rows FROM public_dv_raw.sat_order_details;

-- sample records
SELECT * FROM public_dv_raw.sat_order_details LIMIT 10;

-- null business key hash
SELECT *
FROM public_dv_raw.sat_order_details
WHERE hash_hub_order_id IS NULL;

-- duplicates by nk + load_dts
SELECT hash_hub_cpf, load_dts, COUNT(*) AS record_count
FROM public_dv_raw.sat_user_details_mssql
GROUP BY hash_hub_cpf, load_dts
HAVING COUNT(*) > 1;

-- duplicate hash_diff
SELECT hash_hub_cpf, hash_diff, COUNT(*) AS occurrences
FROM public_dv_raw.sat_user_details_mongodb
GROUP BY hash_hub_cpf, hash_diff
HAVING COUNT(*) > 1;

-- count of versions per order
SELECT
  hash_hub_order_id,
  COUNT(DISTINCT hash_diff) AS version_count
FROM public_dv_raw.sat_order_status
GROUP BY hash_hub_order_id
ORDER BY version_count DESC;

-- latest version per order
SELECT *
FROM (
  SELECT *,
         ROW_NUMBER() OVER (
           PARTITION BY hash_hub_order_id
           ORDER BY load_dts DESC
         ) AS rn
  FROM public_dv_raw.sat_order_status
)
WHERE rn = 1;

-- full change history per order
SELECT
  hash_hub_order_id,
  load_dts,
  status_name,
  status_timestamp,
  status_id,
  hash_diff
FROM public_dv_raw.sat_order_status
ORDER BY hash_hub_order_id, load_dts;

-- detect duplicate versions
SELECT
  hash_hub_order_id,
  hash_diff,
  COUNT(*) AS count
FROM public_dv_raw.sat_order_status
GROUP BY hash_hub_order_id, hash_diff
HAVING COUNT(*) > 1
ORDER BY count DESC;

-- orders with only one version
SELECT
  hash_hub_order_id
FROM public_dv_raw.sat_order_status
GROUP BY hash_hub_order_id
HAVING COUNT(DISTINCT hash_diff) = 1;
