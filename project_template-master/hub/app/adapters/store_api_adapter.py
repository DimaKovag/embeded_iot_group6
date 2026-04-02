import logging
from typing import List

import requests

from app.entities.processed_agent_data import ProcessedAgentData
from app.interfaces.store_gateway import StoreGateway


class StoreApiAdapter(StoreGateway):
    """HTTP-адаптер для збереження оброблених даних у Store API."""

    def __init__(self, api_base_url):
        self.api_base_url = api_base_url

    def save_data(self, processed_agent_data_batch: List[ProcessedAgentData]) -> bool:
        """Надсилає пакет оброблених даних у Store API.

        Parameters
        ----------
        processed_agent_data_batch : list[ProcessedAgentData]
            Список оброблених записів для збереження.

        Returns
        -------
        bool
            True, якщо дані успішно збережені, інакше False.
        """
        if not processed_agent_data_batch:
            return False

        url = f"{self.api_base_url}/processed_agent_data/"
        payload = [item.model_dump(mode="json") for item in processed_agent_data_batch]

        try:
            response = requests.post(url, json=payload, timeout=10)
            success = response.status_code in (200, 201)

            if success:
                logging.info(f"Saved {len(payload)} records to Store API")
            else:
                logging.error(
                    f"Store API error: {response.status_code} - {response.text}"
                )

            return success

        except requests.RequestException as error:
            logging.error(f"Connection error: {error}")
            return False