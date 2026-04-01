from abc import ABC, abstractmethod
from typing import List

from app.entities.processed_agent_data import ProcessedAgentData


class StoreGateway(ABC):
    """Абстрактний інтерфейс шлюзу для збереження даних у store."""

    @abstractmethod
    def save_data(self, processed_agent_data_batch: List[ProcessedAgentData]) -> bool:
        """Зберігає пакет оброблених даних.

        Parameters
        ----------
        processed_agent_data_batch : list[ProcessedAgentData]
            Список оброблених записів.

        Returns
        -------
        bool
            True, якщо дані успішно збережені, інакше False.
        """
        pass