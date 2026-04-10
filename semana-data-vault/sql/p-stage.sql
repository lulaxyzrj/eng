-- 1: create stage to link to blob storage
CREATE STAGE uber_eats_stage
  URL = 'azure://owshqblobstg.blob.core.windows.net/owshq-shadow-traffic-uber-eats/'
  STORAGE_INTEGRATION = azure_blob_ubereats
  CREDENTIALS = (AZURE_SAS_TOKEN = '')
  FILE_FORMAT = (TYPE = 'JSON' STRIP_OUTER_ARRAY = TRUE);

-- 2: create json file format reader
CREATE FILE FORMAT json_format
  TYPE = 'JSON'
  STRIP_OUTER_ARRAY = TRUE;

-- 3: check storage integration configuration
DESC STAGE UberEatsStage;
LIST @UberEatsStage
LIST @UberEatsStage/kafka/orders

-- 4: access files using stage
SELECT $1
FROM @UberEatsStage/kafka/orders (FILE_FORMAT => 'json_format')
WHERE METADATA$FILENAME LIKE '%kafka_orders%'
LIMIT 1;

SELECT
  METADATA$FILENAME AS file_name,
  METADATA$FILE_ROW_NUMBER AS row_number,
  $1:order_id::STRING AS order_id,
  $1:total_amount::FLOAT AS total_amount
FROM @UberEatsStage/kafka/orders (FILE_FORMAT => 'json_format')
WHERE METADATA$FILENAME LIKE '%kafka_orders%'
LIMIT 5;

-- 5: create views
DROP VIEW v_stg_users_mssql;
DROP VIEW v_stg_users_mongodb;
DROP VIEW v_stg_drivers;
DROP VIEW v_stg_restaurants;
DROP VIEW v_stg_orders;
DROP VIEW v_stg_status;

CREATE OR REPLACE VIEW v_stg_users_mssql AS
SELECT
  $1:user_id::INTEGER AS user_id,
  $1:cpf::STRING AS cpf,
  $1:first_name::STRING AS first_name,
  $1:last_name::STRING AS last_name,
  $1:birthday::DATE AS birthday,
  $1:job::STRING AS job,
  $1:phone_number::STRING AS phone_number,
  $1:company_name::STRING AS company_name,
  $1:country::STRING AS country,
  $1:dt_current_timestamp::TIMESTAMP_NTZ(9) AS src_dt_current_timestamp,
  CURRENT_TIMESTAMP()::TIMESTAMP_NTZ(9) AS load_dts,
  METADATA$FILENAME AS file_name,
  'mssql' AS rec_src
FROM @UberEatsStage/mssql/users (FILE_FORMAT => 'json_format');

CREATE OR REPLACE VIEW v_stg_users_mongodb AS
SELECT
  $1:user_id::INTEGER AS user_id,
  $1:cpf::STRING AS cpf,
  $1:city::STRING AS city,
  $1:email::STRING AS email,
  $1:delivery_address::STRING AS delivery_address,
  $1:phone_number::STRING AS phone_number,
  $1:country::STRING AS country,
  $1:dt_current_timestamp::TIMESTAMP_NTZ(9) AS src_dt_current_timestamp,
  CURRENT_TIMESTAMP()::TIMESTAMP_NTZ(9) AS load_dts,
  METADATA$FILENAME AS file_name,
  'mongodb' AS rec_src
FROM @UberEatsStage/mongodb/users (FILE_FORMAT => 'json_format');

CREATE OR REPLACE VIEW v_stg_drivers AS
SELECT
  $1:driver_id::INTEGER AS driver_id,
  $1:license_number::STRING AS license_number,
  $1:first_name::STRING AS first_name,
  $1:last_name::STRING AS last_name,
  $1:date_birth::DATE AS date_birth,
  $1:phone_number::STRING AS phone_number,
  $1:city::STRING AS city,
  $1:country::STRING AS country,
  $1:vehicle_type::STRING AS vehicle_type,
  $1:vehicle_make::STRING AS vehicle_make,
  $1:vehicle_model::STRING AS vehicle_model,
  $1:vehicle_year::INTEGER AS vehicle_year,
  $1:dt_current_timestamp::TIMESTAMP_NTZ(9) AS src_dt_current_timestamp,
  CURRENT_TIMESTAMP()::TIMESTAMP_NTZ(9) AS load_dts,
  METADATA$FILENAME AS file_name,
  'postgres' AS rec_src
FROM @UberEatsStage/postgres/drivers (FILE_FORMAT => 'json_format');

CREATE OR REPLACE VIEW v_stg_restaurants AS
SELECT
  $1:restaurant_id::INTEGER AS restaurant_id,
  $1:cnpj::STRING AS cnpj,
  $1:name::STRING AS name,
  $1:address::STRING AS address,
  $1:city::STRING AS city,
  $1:phone_number::STRING AS phone_number,
  $1:country::STRING AS country,
  $1:cuisine_type::STRING AS cuisine_type,
  $1:opening_time::STRING AS opening_time,
  $1:closing_time::STRING AS closing_time,
  $1:average_rating::FLOAT AS average_rating,
  $1:num_reviews::INTEGER AS num_reviews,
  $1:dt_current_timestamp::TIMESTAMP_NTZ(9) AS src_dt_current_timestamp,
  CURRENT_TIMESTAMP()::TIMESTAMP_NTZ(9) AS load_dts,
  METADATA$FILENAME AS file_name,
  'mysql' AS rec_src
FROM @UberEatsStage/mysql/restaurants (FILE_FORMAT => 'json_format');

CREATE OR REPLACE VIEW v_stg_orders AS
SELECT
  $1:order_id::STRING AS order_id,
  $1:user_key::STRING AS cpf,
  $1:restaurant_key::STRING AS cnpj,
  $1:driver_key::STRING AS license_number,
  $1:order_date::DATETIME AS order_date,
  $1:total_amount::FLOAT AS total_amount,
  $1:payment_key::STRING AS payment_key,
  $1:dt_current_timestamp::TIMESTAMP_NTZ(9) AS src_dt_current_timestamp,
  CURRENT_TIMESTAMP()::TIMESTAMP_NTZ(9) AS load_dts,
  METADATA$FILENAME AS file_name,
  'kafka' AS rec_src
FROM @UberEatsStage/kafka/orders (FILE_FORMAT => 'json_format');

CREATE OR REPLACE VIEW v_stg_status AS
SELECT
  $1:order_identifier::STRING AS order_id,
  $1:status.status_name::STRING AS status_name,
  $1:status.timestamp::BIGINT AS status_timestamp,
  TO_TIMESTAMP_LTZ($1:status.timestamp::BIGINT / 1000) AS status_ts_parsed,
  $1:status_id::INTEGER AS status_id,
  $1:dt_current_timestamp::TIMESTAMP_NTZ(9) AS src_dt_current_timestamp,
  CURRENT_TIMESTAMP()::TIMESTAMP_NTZ(9) AS load_dts,
  METADATA$FILENAME AS file_name,
  'kafka' AS rec_src
FROM @UberEatsStage/kafka/status (FILE_FORMAT => 'json_format');

-- 6: check views and data
SELECT COUNT(*)
FROM v_stg_orders;

SELECT COUNT(*)
FROM v_stg_status;

SELECT order_id, total_amount, src_dt_current_timestamp, load_dts, file_name
FROM v_stg_orders
LIMIT 5;

SELECT *
FROM v_stg_status
LIMIT 5;

/*
DROP TABLE public_dv_raw.hub_drivers;
DROP TABLE public_dv_raw.hub_orders;
DROP TABLE public_dv_raw.hub_restaurants;
DROP TABLE public_dv_raw.hub_users;

DROP TABLE public_dv_raw.link_order_user_restaurant_driver;

DROP TABLE public_dv_raw.sat_driver_details;
DROP TABLE public_dv_raw.sat_order_details;
DROP TABLE public_dv_raw.sat_order_status;
DROP TABLE public_dv_raw.sat_restaurant_details;
DROP TABLE public_dv_raw.sat_user_details_mongodb;
DROP TABLE public_dv_raw.sat_user_details_mssql;
*/

-- change load_dts
CREATE OR REPLACE VIEW v_stg_users_mssql AS
SELECT
  $1:user_id::INTEGER AS user_id,
  $1:cpf::STRING AS cpf,
  $1:first_name::STRING AS first_name,
  $1:last_name::STRING AS last_name,
  $1:birthday::DATE AS birthday,
  $1:job::STRING AS job,
  $1:phone_number::STRING AS phone_number,
  $1:company_name::STRING AS company_name,
  $1:country::STRING AS country,
  $1:dt_current_timestamp::TIMESTAMP_NTZ(9) AS src_dt_current_timestamp,
  CAST('2025-05-26 00:00:00.000000000' AS TIMESTAMP_NTZ(9)) AS load_dts,
  METADATA$FILENAME AS file_name,
  'mssql' AS rec_src
FROM @UberEatsStage/mssql/users (FILE_FORMAT => 'json_format');

CREATE OR REPLACE VIEW v_stg_users_mongodb AS
SELECT
  $1:user_id::INTEGER AS user_id,
  $1:cpf::STRING AS cpf,
  $1:city::STRING AS city,
  $1:email::STRING AS email,
  $1:delivery_address::STRING AS delivery_address,
  $1:phone_number::STRING AS phone_number,
  $1:country::STRING AS country,
  $1:dt_current_timestamp::TIMESTAMP_NTZ(9) AS src_dt_current_timestamp,
  CAST('2025-05-26 00:00:00.000000000' AS TIMESTAMP_NTZ(9)) AS load_dts,
  METADATA$FILENAME AS file_name,
  'mongodb' AS rec_src
FROM @UberEatsStage/mongodb/users (FILE_FORMAT => 'json_format');

CREATE OR REPLACE VIEW v_stg_drivers AS
SELECT
  $1:driver_id::INTEGER AS driver_id,
  $1:license_number::STRING AS license_number,
  $1:first_name::STRING AS first_name,
  $1:last_name::STRING AS last_name,
  $1:date_birth::DATE AS date_birth,
  $1:phone_number::STRING AS phone_number,
  $1:city::STRING AS city,
  $1:country::STRING AS country,
  $1:vehicle_type::STRING AS vehicle_type,
  $1:vehicle_make::STRING AS vehicle_make,
  $1:vehicle_model::STRING AS vehicle_model,
  $1:vehicle_year::INTEGER AS vehicle_year,
  $1:dt_current_timestamp::TIMESTAMP_NTZ(9) AS src_dt_current_timestamp,
  CAST('2025-05-26 00:00:00.000000000' AS TIMESTAMP_NTZ(9)) AS load_dts,
  METADATA$FILENAME AS file_name,
  'postgres' AS rec_src
FROM @UberEatsStage/postgres/drivers (FILE_FORMAT => 'json_format');

CREATE OR REPLACE VIEW v_stg_restaurants AS
SELECT
  $1:restaurant_id::INTEGER AS restaurant_id,
  $1:cnpj::STRING AS cnpj,
  $1:name::STRING AS name,
  $1:address::STRING AS address,
  $1:city::STRING AS city,
  $1:phone_number::STRING AS phone_number,
  $1:country::STRING AS country,
  $1:cuisine_type::STRING AS cuisine_type,
  $1:opening_time::STRING AS opening_time,
  $1:closing_time::STRING AS closing_time,
  $1:average_rating::FLOAT AS average_rating,
  $1:num_reviews::INTEGER AS num_reviews,
  $1:dt_current_timestamp::TIMESTAMP_NTZ(9) AS src_dt_current_timestamp,
  CAST('2025-05-26 00:00:00.000000000' AS TIMESTAMP_NTZ(9)) AS load_dts,
  METADATA$FILENAME AS file_name,
  'mysql' AS rec_src
FROM @UberEatsStage/mysql/restaurants (FILE_FORMAT => 'json_format');

CREATE OR REPLACE VIEW v_stg_orders AS
SELECT
  $1:order_id::STRING AS order_id,
  $1:user_key::STRING AS cpf,
  $1:restaurant_key::STRING AS cnpj,
  $1:driver_key::STRING AS license_number,
  $1:order_date::DATETIME AS order_date,
  $1:total_amount::FLOAT AS total_amount,
  $1:payment_key::STRING AS payment_key,
  $1:dt_current_timestamp::TIMESTAMP_NTZ(9) AS src_dt_current_timestamp,
  CAST('2025-05-26 00:00:00.000000000' AS TIMESTAMP_NTZ(9)) AS load_dts,
  METADATA$FILENAME AS file_name,
  'kafka' AS rec_src
FROM @UberEatsStage/kafka/orders (FILE_FORMAT => 'json_format');

CREATE OR REPLACE VIEW v_stg_status AS
SELECT
  $1:order_identifier::STRING AS order_id,
  $1:status.status_name::STRING AS status_name,
  $1:status.timestamp::BIGINT AS status_timestamp,
  TO_TIMESTAMP_LTZ($1:status.timestamp::BIGINT / 1000) AS status_ts_parsed,
  $1:status_id::INTEGER AS status_id,
  $1:dt_current_timestamp::TIMESTAMP_NTZ(9) AS src_dt_current_timestamp,
  CAST('2025-05-26 00:00:00.000000000' AS TIMESTAMP_NTZ(9)) AS load_dts,
  METADATA$FILENAME AS file_name,
  'kafka' AS rec_src
FROM @UberEatsStage/kafka/status (FILE_FORMAT => 'json_format');
