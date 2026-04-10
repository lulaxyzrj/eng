-- Create schema for raw data
CREATE SCHEMA IF NOT EXISTS UBEREATS.RAW_DATA;
USE SCHEMA UBEREATS.RAW_DATA;

-- Create file format if not exists
CREATE OR REPLACE FILE FORMAT json_format
    TYPE = 'JSON'
    COMPRESSION = 'AUTO'
    ENABLE_OCTAL = FALSE
    ALLOW_DUPLICATE = FALSE
    STRIP_OUTER_ARRAY = FALSE
    STRIP_NULL_VALUES = FALSE
    IGNORE_UTF8_ERRORS = FALSE;

-- 1. Load Users from MSSQL
CREATE OR REPLACE TABLE RAW_USERS_MSSQL AS
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

-- 2. Load Users from MongoDB
CREATE OR REPLACE TABLE RAW_USERS_MONGODB AS
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

-- 3. Load Drivers
CREATE OR REPLACE TABLE RAW_DRIVERS AS
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

-- 4. Load Restaurants
CREATE OR REPLACE TABLE RAW_RESTAURANTS AS
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

-- 5. Load Orders
CREATE OR REPLACE TABLE RAW_ORDERS AS
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

-- 6. Load Status
CREATE OR REPLACE TABLE RAW_STATUS AS
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

-- Verify data loaded
SELECT 'RAW_USERS_MSSQL' as table_name, COUNT(*) as row_count FROM RAW_USERS_MSSQL
UNION ALL
SELECT 'RAW_USERS_MONGODB', COUNT(*) FROM RAW_USERS_MONGODB
UNION ALL
SELECT 'RAW_DRIVERS', COUNT(*) FROM RAW_DRIVERS
UNION ALL
SELECT 'RAW_RESTAURANTS', COUNT(*) FROM RAW_RESTAURANTS
UNION ALL
SELECT 'RAW_ORDERS', COUNT(*) FROM RAW_ORDERS
UNION ALL
SELECT 'RAW_STATUS', COUNT(*) FROM RAW_STATUS

-- 1. Check if stage exists
SHOW STAGES LIKE 'UberEatsStage' IN DATABASE UBEREATS;

-- 2. List files in stage (sample)
LIST @UberEatsStage/mssql/ PATTERN='.*users.*';
LIST @UberEatsStage/mongodb/ PATTERN='.*users.*';
LIST @UberEatsStage/postgres/ PATTERN='.*drivers.*';
LIST @UberEatsStage/mysql/ PATTERN='.*restaurants.*';
LIST @UberEatsStage/kafka/ PATTERN='.*orders.*';

-- 3. Test reading from stage (should return a few rows)
SELECT
    $1:user_id::INTEGER AS user_id,
    $1:cpf::STRING AS cpf
FROM @UberEatsStage/mssql/users (FILE_FORMAT => 'json_format')
LIMIT 5;

-- 4. Check current database and schema
SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ROLE();

-- 5. Verify permissions
SHOW GRANTS ON STAGE UberEatsStage;
