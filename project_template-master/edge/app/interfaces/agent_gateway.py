from abc import ABC, abstractmethod


class AgentGateway(ABC):
    """Абстрактний інтерфейс шлюзу для отримання даних від агента."""

    @abstractmethod
    def on_message(self, client, userdata, msg):
        """Обробляє вхідне повідомлення від агента."""
        pass

    @abstractmethod
    def connect(self):
        """Встановлює з'єднання з джерелом даних агента."""
        pass

    @abstractmethod
    def start(self):
        """Запускає прийом повідомлень від агента."""
        pass

    @abstractmethod
    def stop(self):
        """Зупиняє шлюз агента та звільняє ресурси."""
        pass