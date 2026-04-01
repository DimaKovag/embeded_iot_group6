import logging

from paho.mqtt import client as mqtt_client

from app.entities.processed_agent_data import ProcessedAgentData
from app.interfaces.hub_gateway import HubGateway


class HubMqttAdapter(HubGateway):
    """MQTT-адаптер для передачі оброблених даних у hub."""

    def __init__(self, broker, port, topic):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.mqtt_client = self._connect_mqtt(broker, port)

    def save_data(self, processed_data: ProcessedAgentData) -> bool:
        """Публікує оброблені дані в MQTT-топік hub.

        Parameters
        ----------
        processed_data : ProcessedAgentData
            Оброблені дані агента.

        Returns
        -------
        bool
            True, якщо публікація успішна, інакше False.
        """
        msg = processed_data.model_dump_json()
        result = self.mqtt_client.publish(self.topic, msg)
        status = result[0]

        if status == 0:
            return True

        logging.error(f"Failed to send message to topic {self.topic}")
        return False

    @staticmethod
    def _connect_mqtt(broker, port):
        """Створює та підключає MQTT-клієнт."""
        logging.info(f"CONNECT TO {broker}:{port}")

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logging.info(f"Connected to MQTT Broker ({broker}:{port})!")
            else:
                logging.error(f"Failed to connect {broker}:{port}, return code {rc}")

        client = mqtt_client.Client()
        client.on_connect = on_connect
        client.connect(broker, port)
        client.loop_start()
        return client