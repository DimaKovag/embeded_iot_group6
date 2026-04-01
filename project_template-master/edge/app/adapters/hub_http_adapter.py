import logging

import requests

from app.entities.processed_agent_data import ProcessedAgentData
from app.interfaces.hub_gateway import HubGateway


class HubHttpAdapter(HubGateway):
    """HTTP-адаптер для відправлення оброблених даних у hub."""

    def __init__(self, api_base_url):
        self.api_base_url = api_base_url

    def save_data(self, processed_data: ProcessedAgentData) -> bool:
        """Надсилає оброблені дані в hub через HTTP.

        Parameters
        ----------
        processed_data : ProcessedAgentData
            Оброблені дані агента.

        Returns
        -------
        bool
            True, якщо дані успішно відправлені, інакше False.
        """
        url = f"{self.api_base_url}/processed_agent_data/"

        try:
            response = requests.post(
                url,
                data=processed_data.model_dump_json(),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
        except requests.RequestException as e:
            logging.error(f"Hub HTTP request failed: {e}")
            return False

        if response.status_code != 200:
            logging.error(
                f"Invalid Hub response\n"
                f"Data: {processed_data.model_dump_json()}\n"
                f"Response: {response.status_code} {response.text}"
            )
            return False

        return True