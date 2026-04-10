-- row count and preview
SELECT COUNT(*) FROM v_stg_drivers;
SELECT * FROM v_stg_drivers LIMIT 5;

-- check for nulls in bks
SELECT *
FROM v_stg_drivers
WHERE license_number IS NULL;

-- check business keys duplicates
SELECT license_number, COUNT(*)
FROM v_stg_drivers
GROUP BY license_number
HAVING COUNT(*) > 1;

-- validate temporal profile
SELECT
  DATE_TRUNC('DAY', load_dts) AS load_day,
  COUNT(*) AS records
FROM v_stg_drivers
GROUP BY 1
ORDER BY 1 DESC;

-- file source distribution
SELECT file_name, COUNT(*) AS records
FROM v_stg_users_mssql
GROUP BY file_name
ORDER BY records DESC;

-- version tracking of bks
SELECT cpf, COUNT(DISTINCT load_dts) AS version_count
FROM v_stg_users_mssql
GROUP BY cpf
HAVING version_count > 1;

SELECT license_number, COUNT(DISTINCT load_dts) AS version_count
FROM v_stg_drivers
GROUP BY license_number
HAVING version_count > 1;

SELECT cnpj, COUNT(DISTINCT load_dts) AS version_count
FROM v_stg_restaurants
GROUP BY cnpj
HAVING version_count > 1;

SELECT order_id, COUNT(DISTINCT load_dts) AS version_count
FROM v_stg_orders
GROUP BY order_id
HAVING version_count > 1;

SELECT status_name, COUNT(DISTINCT load_dts) AS version_count
FROM v_stg_status
GROUP BY status_name
HAVING version_count > 1;

-- get latest version per key
SELECT *
FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY status_name ORDER BY load_dts DESC) AS rn
  FROM v_stg_status
)
WHERE rn = 1;
