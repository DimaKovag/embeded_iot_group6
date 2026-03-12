import json
import logging
from typing import List

import pydantic_core
import requests

from app.entities.processed_agent_data import ProcessedAgentData
from app.interfaces.store_gateway import StoreGateway


class StoreApiAdapter(StoreGateway):
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url

    def save_data(self, processed_agent_data_batch: List[ProcessedAgentData]) -> bool:
        # Перевіряємо чи є дані для відправки
        if not processed_agent_data_batch:
            return False

        # Формуємо URL та JSON payload
        url = f"{self.api_base_url}/processed_agent_data/"
        payload = [item.model_dump(mode="json") for item in processed_agent_data_batch]

        try:
            # Виконуємо POST запит до Store API
            response = requests.post(url, json=payload)
            success = response.status_code in [200, 201]

             # Перевіряємо чи запит виконано успішно
            if success:
                logging.info(f"Saved {len(payload)} records to Store API")
            else:
                logging.error(f"Store API error: {response.status_code} - {response.text}")

            return success
        
        except requests.exceptions.RequestException as error:
            logging.error(f"Connection error: {error}")
            return False
