WITH CleanTraffic AS (
    SELECT
        plate_number,
        [timestamp],
        location,
        vehicle_type,
        is_emergency,
        weight_tons,
        speed_kmh,
        speed_limit,
        lane,
        traffic_light,
        is_weekend,
        is_rush_hour,
        accident_in_lane,
        pedestrians_crossing,
        crossed_on_red,
        yellow_light_violation,
        speed_violation,
        seatbelt_worn,
        seatbelt_violation,
        anomaly_detected,
        reckless_driving_anomaly,
        violations,
        traffic_violation_ticket,
        ticket_type,
        CASE
            WHEN traffic_violation_ticket = 1 THEN 1
            ELSE 0
        END AS violation
    FROM [input] TIMESTAMP BY [timestamp]
    WHERE
        speed_kmh >= 0
        AND speed_kmh < 300
        AND location IS NOT NULL
        AND vehicle_type IS NOT NULL
        AND lane IS NOT NULL
        AND traffic_light IS NOT NULL
),
 
WindowedTraffic AS (
    SELECT
        location,
        DATEADD(minute, -5, System.Timestamp()) AS window_start,
        System.Timestamp() AS window_end,
        COUNT(*) AS vehicle_count,
        AVG(speed_kmh) AS avg_speed,
        SUM(CASE WHEN traffic_violation_ticket = 1 THEN 1 ELSE 0 END) AS total_violation_count,
        COUNT(DISTINCT plate_number) AS distinct_plate_count,
        SUM(CASE WHEN crossed_on_red = 1 THEN 1 ELSE 0 END) AS red_light_violation_count,
        SUM(CASE WHEN yellow_light_violation = 1 THEN 1 ELSE 0 END) AS yellow_light_violation_count,
        SUM(CASE WHEN speed_violation = 1 THEN 1 ELSE 0 END) AS speed_violation_count,
        SUM(CASE WHEN seatbelt_violation = 1 THEN 1 ELSE 0 END) AS seatbelt_violation_count,
        SUM(CASE WHEN reckless_driving_anomaly = 1 THEN 1 ELSE 0 END) AS reckless_driving_anomaly_count
    FROM CleanTraffic
    GROUP BY
        location,
        TumblingWindow(minute, 5)
)
 
-- Output 1: violation records with all violation details (to Storage/Container)
SELECT
    plate_number,
    [timestamp],
    location,
    vehicle_type,
    is_emergency,
    weight_tons,
    speed_kmh,
    speed_limit,
    lane,
    traffic_light,
    is_weekend,
    is_rush_hour,
    accident_in_lane,
    pedestrians_crossing,
    crossed_on_red,
    yellow_light_violation,
    speed_violation,
    seatbelt_worn,
    seatbelt_violation,
    anomaly_detected,
    reckless_driving_anomaly,
    violations,
    traffic_violation_ticket,
    ticket_type,
    violation
INTO [violatedcars]
FROM CleanTraffic
WHERE violation = 1;
 
-- Output 2: general traffic summary (to Storage/Container)
SELECT
    location,
    window_start,
    window_end,
    vehicle_count AS total_vehicles,
    avg_speed,
    total_violation_count,
    distinct_plate_count,
    red_light_violation_count,
    yellow_light_violation_count,
    speed_violation_count,
    seatbelt_violation_count,
    reckless_driving_anomaly_count
INTO [generalinfo]
FROM WindowedTraffic;
