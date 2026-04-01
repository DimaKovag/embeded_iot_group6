import logging
import time

from app.adapters.agent_mqtt_adapter import AgentMQTTAdapter
from app.adapters.hub_http_adapter import HubHttpAdapter
from app.adapters.hub_mqtt_adapter import HubMqttAdapter
from config import (
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
    MQTT_TOPIC,
    HUB_URL,
    HUB_MQTT_BROKER_HOST,
    HUB_MQTT_BROKER_PORT,
    HUB_MQTT_TOPIC,
)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("app.log"),
        ],
    )

    # hub_adapter = HubHttpAdapter(api_base_url=HUB_URL)
    hub_adapter = HubMqttAdapter(
        broker=HUB_MQTT_BROKER_HOST,
        port=HUB_MQTT_BROKER_PORT,
        topic=HUB_MQTT_TOPIC,
    )

    agent_adapter = AgentMQTTAdapter(
        broker_host=MQTT_BROKER_HOST,
        broker_port=MQTT_BROKER_PORT,
        topic=MQTT_TOPIC,
        hub_gateway=hub_adapter,
    )

    try:
        agent_adapter.connect()
        agent_adapter.start()

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent_adapter.stop()
        logging.info("System stopped.")