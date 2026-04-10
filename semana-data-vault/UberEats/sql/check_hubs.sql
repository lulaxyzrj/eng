-- check count and data
SELECT COUNT(*) FROM public_dv_raw.hub_drivers;
SELECT * FROM public_dv_raw.hub_drivers LIMIT 5;

-- business key null check
SELECT *
FROM public_dv_raw.hub_drivers
WHERE license_number IS NULL;

SELECT *
FROM public_dv_raw.hub_users
WHERE cpf IS NULL;

-- hash key validation
SELECT hash_hub_license_number, COUNT(*)
FROM public_dv_raw.hub_drivers
GROUP BY hash_hub_license_number
HAVING COUNT(*) > 1;

SELECT hash_hub_cpf, COUNT(*)
FROM public_dv_raw.hub_users
GROUP BY hash_hub_cpf
HAVING COUNT(*) > 1;

-- null hash check
SELECT *
FROM public_dv_raw.hub_drivers
WHERE hash_hub_license_number IS NULL;

-- load timestamp profiling
SELECT
  DATE_TRUNC('DAY', load_dts) AS load_day,
  COUNT(*) AS records
FROM public_dv_raw.hub_drivers
GROUP BY 1
ORDER BY 1 DESC;

SELECT
  DATE_TRUNC('DAY', load_dts) AS load_day,
  COUNT(*) AS records
FROM public_dv_raw.hub_users
GROUP BY 1
ORDER BY 1 DESC;
