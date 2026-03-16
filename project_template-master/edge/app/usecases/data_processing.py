from collections import deque

from app.entities.agent_data import AgentData
from app.entities.processed_agent_data import ProcessedAgentData
from config import ROAD_AXIS, SMOOTHING_WINDOW, SMOOTH_THRESHOLD, UNEVEN_THRESHOLD


_recent_values = deque(maxlen=SMOOTHING_WINDOW)


def _get_axis_value(agent_data: AgentData) -> float:
    axis = ROAD_AXIS.lower()

    if axis == "x":
        return float(agent_data.accelerometer.x)
    if axis == "y":
        return float(agent_data.accelerometer.y)
    if axis == "z":
        return float(agent_data.accelerometer.z)

    raise ValueError(f"Unsupported ROAD_AXIS value: {ROAD_AXIS}")


def _classify_road_state(smoothed_abs_value: float) -> tuple[str, str]:
    """
    Returns:
        tuple[str, str]: (road_state, severity)
    """

    if smoothed_abs_value < SMOOTH_THRESHOLD:
        return "smooth", "low"

    if smoothed_abs_value < UNEVEN_THRESHOLD:
        return "uneven", "medium"

    return "pothole", "high"


def reset_processing_state() -> None:
    """
    Helper for tests. Clears smoothing buffer.
    """
    _recent_values.clear()


def process_agent_data(agent_data: AgentData) -> ProcessedAgentData:
    """
    Process agent data and classify the state of the road surface.

    Logic:
    - takes configured accelerometer axis (x/y/z)
    - stores the latest values in a sliding window
    - calculates average of the last N values
    - classifies road state by threshold ranges

    Parameters:
        agent_data (AgentData): Agent data containing accelerometer, GPS and timestamp.

    Returns:
        ProcessedAgentData: Processed data containing classified road state,
        severity level, smoothed value and original agent data.
    """

    axis_value = _get_axis_value(agent_data)
    _recent_values.append(axis_value)

    smoothed_value = sum(_recent_values) / len(_recent_values)
    smoothed_abs_value = abs(smoothed_value)

    road_state, severity = _classify_road_state(smoothed_abs_value)

    return ProcessedAgentData(
        road_state=road_state,
        severity=severity,
        smoothed_value=smoothed_value,
        agent_data=agent_data,
    )