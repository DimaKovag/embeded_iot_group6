from collections import deque

from app.entities.agent_data import AgentData
from app.entities.processed_agent_data import ProcessedAgentData
from config import (
    ROAD_AXIS,
    SMOOTHING_WINDOW,
    Z_BASELINE,
    SMOOTH_THRESHOLD,
    BUMP_THRESHOLD,
)


_recent_values = deque(maxlen=max(1, SMOOTHING_WINDOW))


def _get_axis_value(agent_data: AgentData) -> float:
    """Повертає значення вибраної осі акселерометра.

    Parameters
    ----------
    agent_data : AgentData
        Вхідні дані агента.

    Returns
    -------
    float
        Значення вибраної осі акселерометра.

    Raises
    ------
    ValueError
        Якщо значення ROAD_AXIS не підтримується.
    """
    axis = ROAD_AXIS.lower()

    if axis == "x":
        return float(agent_data.accelerometer.x)
    if axis == "y":
        return float(agent_data.accelerometer.y)
    if axis == "z":
        return float(agent_data.accelerometer.z)

    raise ValueError(f"Unsupported ROAD_AXIS value: {ROAD_AXIS}")


def _classify_road_state(delta_value: float) -> tuple[str, str]:
    """Класифікує стан дороги за відхиленням по осі.

    Parameters
    ----------
    delta_value : float
        Абсолютне відхилення від базового значення.

    Returns
    -------
    tuple[str, str]
        Пара значень: стан дороги та рівень серйозності.
    """
    if delta_value < SMOOTH_THRESHOLD:
        return "smooth", "low"
    if delta_value < BUMP_THRESHOLD:
        return "bump", "medium"
    return "pothole", "high"


def reset_processing_state() -> None:
    """Очищає внутрішній буфер згладжування."""
    _recent_values.clear()


def process_agent_data(agent_data: AgentData) -> ProcessedAgentData:
    """Обробляє дані агента та визначає стан дороги.

    Parameters
    ----------
    agent_data : AgentData
        Вхідні дані агента.

    Returns
    -------
    ProcessedAgentData
        Оброблені дані зі станом дороги, серйозністю та згладженим значенням.
    """
    axis_value = _get_axis_value(agent_data)
    _recent_values.append(axis_value)

    smoothed_value = sum(_recent_values) / len(_recent_values)
    delta_value = abs(smoothed_value - Z_BASELINE)

    road_state, severity = _classify_road_state(delta_value)

    return ProcessedAgentData(
        road_state=road_state,
        severity=severity,
        smoothed_value=delta_value,
        agent_data=agent_data,
    )