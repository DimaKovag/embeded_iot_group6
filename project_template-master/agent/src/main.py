from paho.mqtt import client as mqtt_client
import time

from schema.aggregated_data_schema import AggregatedDataSchema
from file_datasource import FileDatasource
import config


def connect_mqtt(broker, port):
    """Створює та підключає MQTT-клієнт.

    Parameters
    ----------
    broker : str
        Адреса MQTT-брокера.
    port : int
        Порт MQTT-брокера.

    Returns
    -------
    mqtt_client.Client
        Ініціалізований MQTT-клієнт.
    """
    print(f"CONNECT TO {broker}:{port}")

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to MQTT Broker ({broker}:{port})!")
        else:
            print(f"Failed to connect {broker}:{port}, return code {rc}")
            raise ConnectionError(f"MQTT connection failed with code {rc}")

    client = mqtt_client.Client()
    client.on_connect = on_connect
    client.connect(broker, port)
    client.loop_start()
    return client


def publish(client, topic, datasource, delay):
    """Публікує агреговані дані в MQTT-топік із заданою затримкою.

    Parameters
    ----------
    client : mqtt_client.Client
        MQTT-клієнт.
    topic : str
        Назва топіка для публікації.
    datasource : FileDatasource
        Джерело даних для зчитування повідомлень.
    delay : int | float
        Затримка між публікаціями у секундах.
    """
    datasource.startReading()
    try:
        while True:
            time.sleep(delay)
            data = datasource.read()
            msg = AggregatedDataSchema().dumps(data)
            result = client.publish(topic, msg)
            status = result[0]

            if status != 0:
                print(f"Failed to send message to topic {topic}")
    finally:
        datasource.stopReading()
        client.loop_stop()


def run():
    """Запускає агент публікації даних."""
    client = connect_mqtt(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT)
    datasource = FileDatasource(
        "data/accelerometer.csv",
        "data/gps.csv",
        "data/parking.csv"
    )
    publish(client, config.MQTT_TOPIC, datasource, 1)


if __name__ == "__main__":
    run()