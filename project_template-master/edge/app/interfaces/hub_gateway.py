from abc import ABC, abstractmethod

from app.entities.processed_agent_data import ProcessedAgentData


class HubGateway(ABC):
    """Абстрактний інтерфейс шлюзу для передачі даних у hub."""

    @abstractmethod
    def save_data(self, processed_data: ProcessedAgentData) -> bool:
        """Зберігає або передає оброблені дані агента в hub.
        """
        pass