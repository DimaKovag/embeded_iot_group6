import logging

import paho.mqtt.client as mqtt

from app.entities.agent_data import AgentData
from app.interfaces.agent_gateway import AgentGateway
from app.interfaces.hub_gateway import HubGateway
from app.usecases.data_processing import process_agent_data


class AgentMQTTAdapter(AgentGateway):
    """MQTT-адаптер для прийому даних агента та передачі їх у hub."""

    def __init__(
        self,
        broker_host,
        broker_port,
        topic,
        hub_gateway: HubGateway,
        batch_size=10,
    ):
        self.batch_size = batch_size
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.client = mqtt.Client()
        self.hub_gateway = hub_gateway

    def on_connect(self, client, userdata, flags, rc):
        """Обробляє підключення до MQTT-брокера."""
        if rc == 0:
            logging.info("Connected to MQTT broker")
            client.subscribe(self.topic)
        else:
            logging.error(f"Failed to connect to MQTT broker with code: {rc}")

    def on_message(self, client, userdata, msg):
        """Обробляє MQTT-повідомлення від агента.

        Parameters
        ----------
        client :
            Екземпляр MQTT-клієнта.
        userdata :
            Додаткові користувацькі дані MQTT.
        msg :
            Отримане MQTT-повідомлення.
        """
        try:
            payload = msg.payload.decode("utf-8")
            agent_data = AgentData.model_validate_json(payload, strict=True)
            processed_data = process_agent_data(agent_data)

            if not self.hub_gateway.save_data(processed_data):
                logging.error("Hub is not available")
        except Exception as e:
            logging.exception(f"Error processing MQTT message: {e}")

    def connect(self):
        """Налаштовує callback-и та підключається до брокера."""
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_host, self.broker_port, 60)

    def start(self):
        """Запускає цикл обробки MQTT-повідомлень."""
        self.client.loop_start()

    def stop(self):
        """Зупиняє цикл MQTT та відключає клієнт."""
        self.client.loop_stop()
        self.client.disconnect()