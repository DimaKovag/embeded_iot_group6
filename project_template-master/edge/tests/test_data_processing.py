from datetime import datetime

from app.entities.agent_data import AgentData, AccelerometerData, GpsData
from app.usecases.data_processing import process_agent_data, reset_processing_state


def make_agent_data(z: float) -> AgentData:
    return AgentData(
        accelerometer=AccelerometerData(x=0.0, y=0.0, z=z),
        gps=GpsData(latitude=48.2921, longitude=25.9358),
        timestamp=datetime.fromisoformat("2026-03-13T12:00:00"),
    )


def test_smooth_classification():
    reset_processing_state()

    result = process_agent_data(make_agent_data(1.0))

    assert result.road_state == "smooth"
    assert result.severity == "low"
    assert result.smoothed_value == 1.0


def test_uneven_classification_with_average_of_last_three():
    reset_processing_state()

    process_agent_data(make_agent_data(1.0))
    process_agent_data(make_agent_data(3.0))
    result = process_agent_data(make_agent_data(4.0))

    # average = (1 + 3 + 4) / 3 = 2.666...
    assert result.road_state == "uneven"
    assert result.severity == "medium"
    assert 2.6 < result.smoothed_value < 2.7


def test_pothole_classification_with_average_of_last_three():
    reset_processing_state()

    process_agent_data(make_agent_data(5.0))
    process_agent_data(make_agent_data(6.0))
    result = process_agent_data(make_agent_data(7.0))

    # average = 6.0
    assert result.road_state == "pothole"
    assert result.severity == "high"
    assert result.smoothed_value == 6.0


def test_sliding_window_keeps_only_last_three_values():
    reset_processing_state()

    process_agent_data(make_agent_data(1.0))
    process_agent_data(make_agent_data(1.0))
    process_agent_data(make_agent_data(1.0))
    result = process_agent_data(make_agent_data(7.0))

    # last three are 1, 1, 7 => average = 3.0
    assert result.road_state == "uneven"
    assert result.severity == "medium"
    assert result.smoothed_value == 3.0


def test_negative_values_are_classified_by_absolute_value():
    reset_processing_state()

    process_agent_data(make_agent_data(-6.0))
    process_agent_data(make_agent_data(-6.0))
    result = process_agent_data(make_agent_data(-6.0))

    assert result.road_state == "pothole"
    assert result.severity == "high"
    assert result.smoothed_value == -6.0