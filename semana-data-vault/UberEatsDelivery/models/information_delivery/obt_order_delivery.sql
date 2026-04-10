{{ config(
    materialized='table',
    tags=['information_delivery', 'obt']
) }}

WITH order_base AS (
    SELECT
        h.ORDER_HK,
        h.ORDER_ID,
        h.LOAD_DTS AS ORDER_FIRST_SEEN
    FROM {{ ref('hub_order') }} h
),

order_details AS (
    SELECT
        ORDER_HK,
        TOTAL_AMOUNT,
        ORDER_DATE,
        PAYMENT_KEY,
        LOAD_DTS
    FROM {{ ref('sat_order_details') }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY ORDER_HK ORDER BY LOAD_DTS DESC) = 1
),

order_driver AS (
    SELECT
        lod.ORDER_HK,
        lod.DRIVER_HK,
        hd.LICENSE_NUMBER,
        sd.FIRST_NAME AS DRIVER_FIRST_NAME,
        sd.LAST_NAME AS DRIVER_LAST_NAME,
        sd.VEHICLE_TYPE,
        sd.CITY AS DRIVER_CITY
    FROM {{ ref('link_order_driver') }} lod
    JOIN {{ ref('hub_driver') }} hd ON lod.DRIVER_HK = hd.DRIVER_HK
    LEFT JOIN {{ ref('sat_driver_details') }} sd ON hd.DRIVER_HK = sd.DRIVER_HK
    QUALIFY ROW_NUMBER() OVER (PARTITION BY sd.DRIVER_HK ORDER BY sd.LOAD_DTS DESC) = 1
),

order_status_timeline AS (
    SELECT
        ORDER_HK,
        MAX(CASE WHEN STATUS_NAME = 'Order Placed' THEN STATUS_TIMESTAMP END) AS order_placed_time,
        MAX(CASE WHEN STATUS_NAME = 'Accepted' THEN STATUS_TIMESTAMP END) AS accepted_time,
        MAX(CASE WHEN STATUS_NAME = 'Preparing' THEN STATUS_TIMESTAMP END) AS preparing_time,
        MAX(CASE WHEN STATUS_NAME = 'Ready for Pickup' THEN STATUS_TIMESTAMP END) AS ready_time,
        MAX(CASE WHEN STATUS_NAME = 'Picked Up' THEN STATUS_TIMESTAMP END) AS pickup_time,
        MAX(CASE WHEN STATUS_NAME = 'Out for Delivery' THEN STATUS_TIMESTAMP END) AS out_for_delivery_time,
        MAX(CASE WHEN STATUS_NAME = 'Delivered' THEN STATUS_TIMESTAMP END) AS delivered_time,
        COUNT(DISTINCT STATUS_NAME) AS total_status_changes
    FROM {{ ref('sat_order_status') }}
    GROUP BY ORDER_HK
),

current_status AS (
    SELECT
        ORDER_HK,
        STATUS_NAME AS CURRENT_STATUS,
        STATUS_TIMESTAMP AS LAST_STATUS_UPDATE
    FROM {{ ref('sat_order_status') }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY ORDER_HK ORDER BY STATUS_TIMESTAMP DESC) = 1
)

SELECT
    ob.ORDER_ID,
    od.ORDER_DATE,
    od.TOTAL_AMOUNT,
    od.PAYMENT_KEY,

    odr.LICENSE_NUMBER AS DRIVER_LICENSE,
    odr.DRIVER_FIRST_NAME,
    odr.DRIVER_LAST_NAME,
    odr.VEHICLE_TYPE,
    odr.DRIVER_CITY,

    cs.CURRENT_STATUS,
    cs.LAST_STATUS_UPDATE,

    ost.order_placed_time,
    ost.accepted_time,
    ost.preparing_time,
    ost.ready_time,
    ost.pickup_time,
    ost.out_for_delivery_time,
    ost.delivered_time,
    ost.total_status_changes,

    DATEDIFF('minute', ost.order_placed_time::TIMESTAMP, ost.accepted_time::TIMESTAMP) AS time_to_accept_minutes,
    DATEDIFF('minute', ost.accepted_time::TIMESTAMP, ost.ready_time::TIMESTAMP) AS preparation_time_minutes,
    DATEDIFF('minute', ost.ready_time::TIMESTAMP, ost.pickup_time::TIMESTAMP) AS wait_for_pickup_minutes,
    DATEDIFF('minute', ost.pickup_time::TIMESTAMP, ost.delivered_time::TIMESTAMP) AS delivery_time_minutes,
    DATEDIFF('minute', ost.order_placed_time::TIMESTAMP, ost.delivered_time::TIMESTAMP) AS total_order_time_minutes,

    CASE
        WHEN ost.delivered_time IS NOT NULL THEN 'Completed'
        WHEN cs.CURRENT_STATUS IN ('Order Placed', 'In Analysis') THEN 'Processing'
        WHEN cs.CURRENT_STATUS IN ('Accepted', 'Preparing', 'Ready for Pickup') THEN 'In Restaurant'
        WHEN cs.CURRENT_STATUS IN ('Picked Up', 'Out for Delivery') THEN 'In Transit'
        ELSE 'Unknown'
    END AS ORDER_STAGE,

    CASE
        WHEN DATEDIFF('minute', ost.order_placed_time::TIMESTAMP, ost.delivered_time::TIMESTAMP) <= 30 THEN 'Excellent'
        WHEN DATEDIFF('minute', ost.order_placed_time::TIMESTAMP, ost.delivered_time::TIMESTAMP) <= 45 THEN 'Good'
        WHEN DATEDIFF('minute', ost.order_placed_time::TIMESTAMP, ost.delivered_time::TIMESTAMP) <= 60 THEN 'Fair'
        WHEN ost.delivered_time IS NOT NULL THEN 'Poor'
        ELSE 'In Progress'
    END AS DELIVERY_PERFORMANCE,

    ob.ORDER_FIRST_SEEN,
    CURRENT_TIMESTAMP() AS OBT_LOAD_DTS

FROM order_base ob
LEFT JOIN order_details od ON ob.ORDER_HK = od.ORDER_HK
LEFT JOIN order_driver odr ON ob.ORDER_HK = odr.ORDER_HK
LEFT JOIN order_status_timeline ost ON ob.ORDER_HK = ost.ORDER_HK
LEFT JOIN current_status cs ON ob.ORDER_HK = cs.ORDER_HK