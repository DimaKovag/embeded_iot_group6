import logging
from typing import List

from fastapi import FastAPI
import paho.mqtt.client as mqtt
from redis import Redis

from app.adapters.store_api_adapter import StoreApiAdapter
from app.entities.processed_agent_data import ProcessedAgentData
from config import (
    STORE_API_BASE_URL,
    REDIS_HOST,
    REDIS_PORT,
    BATCH_SIZE,
    MQTT_TOPIC,
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
)


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log"),
    ],
)

redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT)
store_adapter = StoreApiAdapter(api_base_url=STORE_API_BASE_URL)

app = FastAPI()
client = mqtt.Client()


def _push_to_queue(processed_agent_data: ProcessedAgentData) -> None:
    """Додає запис у Redis-чергу.

    Parameters
    ----------
    processed_agent_data : ProcessedAgentData
        Оброблені дані агента.
    """
    redis_client.lpush("processed_agent_data", processed_agent_data.model_dump_json())


def _decode_redis_item(item) -> str:
    """Перетворює значення з Redis у рядок JSON."""
    if isinstance(item, bytes):
        return item.decode("utf-8")
    return item


def _peek_batch(batch_size: int) -> List[ProcessedAgentData]:
    """Зчитує пакет даних із Redis без видалення.

    Parameters
    ----------
    batch_size : int
        Розмір пакета.

    Returns
    -------
    list[ProcessedAgentData]
        Список записів для відправки.
    """
    items = redis_client.lrange("processed_agent_data", 0, batch_size - 1)
    result: List[ProcessedAgentData] = []

    for item in items:
        result.append(
            ProcessedAgentData.model_validate_json(_decode_redis_item(item), strict=True)
        )

    return result


def _remove_batch(batch_size: int) -> None:
    """Видаляє успішно відправлений пакет із Redis."""
    redis_client.ltrim("processed_agent_data", batch_size, -1)


def _flush_batch_if_needed() -> bool:
    """Надсилає пакет у Store, якщо в черзі достатньо записів.

    Returns
    -------
    bool
        True, якщо пакет успішно відправлено або якщо пакет ще не готовий.
        False, якщо відправлення завершилось помилкою.
    """
    queue_name = "processed_agent_data"

    if redis_client.llen(queue_name) < BATCH_SIZE:
        return True

    batch = _peek_batch(BATCH_SIZE)
    if not batch:
        return True

    success = store_adapter.save_data(processed_agent_data_batch=batch)
    if success:
        _remove_batch(BATCH_SIZE)
        logging.info(f"Flushed batch of {len(batch)} records to Store API")
        return True

    logging.error("Failed to flush batch to Store API")
    return False


@app.post("/processed_agent_data/")
async def save_processed_agent_data(processed_agent_data: ProcessedAgentData):
    """Приймає оброблені дані через HTTP та додає їх у Redis-чергу."""
    _push_to_queue(processed_agent_data)
    _flush_batch_if_needed()
    return {"status": "ok"}


def on_connect(client, userdata, flags, rc):
    """Обробляє підключення до MQTT-брокера."""
    if rc == 0:
        logging.info("Connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
    else:
        logging.error(f"Failed to connect to MQTT broker with code: {rc}")


def on_message(client, userdata, msg):
    """Обробляє MQTT-повідомлення з processed_agent_data.

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
        processed_agent_data = ProcessedAgentData.model_validate_json(
            payload,
            strict=True,
        )

        _push_to_queue(processed_agent_data)
        _flush_batch_if_needed()

    except Exception as e:
        logging.exception(f"Error processing MQTT message: {e}")


client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
client.loop_start()