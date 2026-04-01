from datetime import datetime

from pydantic import BaseModel, field_validator


class AccelerometerData(BaseModel):
    """Модель даних акселерометра."""
    x: float
    y: float
    z: float


class GpsData(BaseModel):
    """Модель GPS-координат."""
    latitude: float
    longitude: float


class AgentData(BaseModel):
    """Модель сирих даних, отриманих від агента."""
    user_id: int
    accelerometer: AccelerometerData
    gps: GpsData
    timestamp: datetime

    @classmethod
    @field_validator("timestamp", mode="before")
    def parse_timestamp(cls, value):
        """Перетворює timestamp у datetime.

        Parameters
        ----------
        value : str | datetime
            Вхідне значення часової мітки.

        Returns
        -------
        datetime
            Валідований об'єкт datetime.

        Raises
        ------
        ValueError
            Якщо формат часової мітки некоректний.
        """
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            value = value.replace("Z", "+00:00")

        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError(
                "Invalid timestamp format. Expected ISO 8601 format."
            )