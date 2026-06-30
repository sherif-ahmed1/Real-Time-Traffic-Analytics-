import json
import time
import random
from datetime import datetime
from pathlib import Path
import pytz
from azure.eventhub import EventHubProducerClient, EventData

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    config = json.load(file)

producer = EventHubProducerClient.from_connection_string(
    conn_str=config["azure_connection_string"],
    eventhub_name=config["event_hub_name"]
)

def generate_egyptian_plate():
    letters = ['أ', 'ب', 'ت', 'ث', 'ج', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ك', 'ل', 'م', 'ن', 'ه', 'و', 'ي']
    plate_letters = " ".join(random.choices(letters, k=3))
    plate_numbers = "".join(random.choices("123456789", k=4))
    return f"{plate_letters} {plate_numbers}"

def get_traffic_light(current_timestamp):
    durations = config["traffic_light_durations"]
    total_cycle = durations["green"] + durations["red"] + durations["yellow"]
    cycle = int(current_timestamp) % total_cycle

    if cycle < durations["green"]:
        return "Green"
    elif cycle < (durations["green"] + durations["red"]):
        return "Red"
    else:
        return "Yellow"

def is_seatbelt_applicable(vehicle_type):
    non_seatbelt_types = {"Motorcycle", "Bicycle", "Scooter"}
    return vehicle_type not in non_seatbelt_types

def build_ticket_from_violations(violations):
    return " | ".join(violations) if violations else None

def generate_car_data():
    cairo_tz = pytz.timezone("Africa/Cairo")
    current_timestamp = time.time()
    current_time = datetime.fromtimestamp(current_timestamp, cairo_tz)

    is_weekend = current_time.weekday() in [4, 5]
    is_rush_hour = False if is_weekend else (16 <= current_time.hour < 20)

    traffic_light = get_traffic_light(current_timestamp)
    lane = random.choice(config["lanes"])

    is_emergency = random.random() < 0.05
    if is_emergency:
        v_type = random.choice(config["emergency_vehicles"])
    else:
        v_type = random.choice(config["vehicle_types"])

    weight_tons = round(random.uniform(15.0, 60.0), 2) if v_type == "Heavy Truck" else 0.0

    has_accident = random.random() < config["accident_probability"]
    pedestrians_crossing = random.random() < config["pedestrian_crossing_probability"]

    speed_limit = 80

    if has_accident:
        speed = 0
    elif is_emergency:
        speed = random.randint(90, 140)
    elif pedestrians_crossing:
        speed = random.randint(5, 15)
    else:
        if traffic_light == "Red":
            if random.random() < config["red_light_violation_probability"]:
                speed = random.randint(15, 45)
            else:
                speed = random.randint(0, 5)

        elif traffic_light == "Yellow":
            if random.random() < config["yellow_light_violation_probability"]:
                speed = random.randint(30, 70)
            else:
                speed = random.randint(10, 25)

        else:  # Green
            if is_rush_hour:
                speed = random.randint(*config["rush_hour_speed_range"])
            else:
                speed = random.randint(*config["normal_speed_range"])

    anomaly_detected = False
    anomaly_speed = False
    anomaly_lane = False

    if random.random() < config["anomaly_probability"] and not has_accident:
        anomaly_detected = True

        if random.random() < 0.5:
            speed = random.choice([-20, 250, 300])
            anomaly_speed = True

        if random.random() < 0.5:
            lane = random.choice([7, 8, 9])
            anomaly_lane = True

    crossed_on_red = (
        traffic_light == "Red"
        and speed > 5
        and not is_emergency
        and not has_accident
        and not pedestrians_crossing
    )

    yellow_light_violation = (
        traffic_light == "Yellow"
        and speed >= 30
        and not is_emergency
        and not has_accident
        and not pedestrians_crossing
    )

    speed_violation = (
        speed > speed_limit
        and not is_emergency
        and speed < 200
    )

    if is_seatbelt_applicable(v_type) and not is_emergency:
        seatbelt_worn = random.random() >= config.get("seatbelt_violation_probability", 0.08)
        seatbelt_violation = not seatbelt_worn
    else:
        seatbelt_worn = None
        seatbelt_violation = False

    reckless_driving_anomaly = speed in [120, 300]

    violations = []

    if crossed_on_red:
        violations.append("Red Light Violation")

    if yellow_light_violation:
        violations.append("Unsafe Yellow Crossing")

    if speed_violation:
        violations.append("Speed Limit Violation")

    if seatbelt_violation:
        violations.append("Seatbelt Violation")

    if reckless_driving_anomaly:
        violations.append("Reckless Driving (Anomaly)")

    traffic_violation_ticket = 1 if len(violations) > 0 else 0
    ticket_type = build_ticket_from_violations(violations)

    return {
        "plate_number": generate_egyptian_plate(),
        "timestamp": current_time.isoformat(),
        "location": config["location"],
        "vehicle_type": v_type,
        "is_emergency": is_emergency,
        "weight_tons": weight_tons,
        "speed_kmh": speed,
        "speed_limit": speed_limit,
        "lane": lane,
        "traffic_light": traffic_light,
        "is_weekend": is_weekend,
        "is_rush_hour": is_rush_hour,
        "accident_in_lane": has_accident,
        "pedestrians_crossing": pedestrians_crossing,
        "crossed_on_red": crossed_on_red,
        "yellow_light_violation": yellow_light_violation,
        "speed_violation": speed_violation,
        "seatbelt_worn": seatbelt_worn,
        "seatbelt_violation": seatbelt_violation,
        "anomaly_detected": anomaly_detected,
        "anomaly_speed": anomaly_speed,
        "anomaly_lane": anomaly_lane,
        "reckless_driving_anomaly": reckless_driving_anomaly,
        "violations": violations,
        "traffic_violation_ticket": traffic_violation_ticket,
        "ticket_type": ticket_type
    }

def run_generator():
    try:
        while True:
            for _ in range(2):
                car_data = generate_car_data()
                json_data = json.dumps(car_data, ensure_ascii=False)

                event_data_batch = producer.create_batch()
                event_data_batch.add(EventData(json_data))
                producer.send_batch(event_data_batch)

                print(f"[SENT] {json_data}\n")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStream stopped.")

if __name__ == "__main__":
    run_generator()
