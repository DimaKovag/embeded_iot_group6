import os


def try_parse_int(value: str):
    try:
        return int(value)
    except Exception:
        return None
    
def try_parse_float(value: str | None):
    try:
        return float(value) if value is not None else None
    except Exception:
        return None


# Configuration for agent MQTT
MQTT_BROKER_HOST = os.environ.get("MQTT_BROKER_HOST") or "localhost"
MQTT_BROKER_PORT = try_parse_int(os.environ.get("MQTT_BROKER_PORT")) or 1883
MQTT_TOPIC = os.environ.get("MQTT_TOPIC") or "agent_data_topic"

# Configuration for hub MQTT
HUB_MQTT_BROKER_HOST = os.environ.get("HUB_MQTT_BROKER_HOST") or "localhost"
HUB_MQTT_BROKER_PORT = try_parse_int(os.environ.get("HUB_MQTT_BROKER_PORT")) or 1883
HUB_MQTT_TOPIC = os.environ.get("HUB_MQTT_TOPIC") or "processed_agent_data_topic"

# Configuration for the Hub
HUB_HOST = os.environ.get("HUB_HOST") or "localhost"
HUB_PORT = try_parse_int(os.environ.get("HUB_PORT")) or 12000
HUB_URL = f"http://{HUB_HOST}:{HUB_PORT}"

# Configuration for data processing
ROAD_AXIS = os.environ.get("ROAD_AXIS") or "z"

SMOOTHING_WINDOW = try_parse_int(os.environ.get("SMOOTHING_WINDOW")) or 3
SMOOTH_THRESHOLD = try_parse_float(os.environ.get("SMOOTH_THRESHOLD")) or 2.0
UNEVEN_THRESHOLD = try_parse_float(os.environ.get("UNEVEN_THRESHOLD")) or 5.0