from pydantic import BaseModel
from app.entities.agent_data import AgentData


class ProcessedAgentData(BaseModel):
    road_state: str
    severity: str
    smoothed_value: float
    agent_data: AgentData