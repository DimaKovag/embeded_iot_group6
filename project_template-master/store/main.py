import json
from datetime import datetime
from typing import Dict, List, Set

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, field_validator
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
)
from sqlalchemy.orm import sessionmaker

from config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)


app = FastAPI()

DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
engine = create_engine(DATABASE_URL)
metadata = MetaData()

processed_agent_data = Table(
    "processed_agent_data",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("road_state", String),
    Column("user_id", Integer),
    Column("x", Float),
    Column("y", Float),
    Column("z", Float),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("timestamp", DateTime),
)

metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


class ProcessedAgentDataInDB(BaseModel):
    """Модель запису processed_agent_data, що повертається з БД."""
    id: int
    road_state: str
    user_id: int
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime


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
    """Модель сирих даних агента."""
    user_id: int
    accelerometer: AccelerometerData
    gps: GpsData
    timestamp: datetime

    @classmethod
    @field_validator("timestamp", mode="before")
    def check_timestamp(cls, value):
        """Перетворює timestamp у datetime."""
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            value = value.replace("Z", "+00:00")

        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError("Invalid timestamp format. Expected ISO 8601 format.")


class ProcessedAgentData(BaseModel):
    """Модель оброблених даних агента."""
    road_state: str
    agent_data: AgentData


subscriptions: Dict[int, Set[WebSocket]] = {}


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """Реєструє WebSocket-клієнта для отримання даних конкретного користувача."""
    await websocket.accept()
    subscriptions.setdefault(user_id, set()).add(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        if user_id in subscriptions:
            subscriptions[user_id].discard(websocket)
            if not subscriptions[user_id]:
                subscriptions.pop(user_id, None)


async def send_data_to_subscribers(user_id: int, data: dict) -> None:
    """Надсилає дані всім WebSocket-підписникам користувача.

    Parameters
    ----------
    user_id : int
        Ідентифікатор користувача.
    data : dict
        Дані для відправлення.
    """
    sockets = subscriptions.get(user_id, set()).copy()
    disconnected = []

    for websocket in sockets:
        try:
            await websocket.send_json(data)
        except Exception:
            disconnected.append(websocket)

    for websocket in disconnected:
        subscriptions.get(user_id, set()).discard(websocket)


@app.post("/processed_agent_data/")
async def create_processed_agent_data(data: List[ProcessedAgentData]):
    """Зберігає пакет оброблених даних та розсилає їх WebSocket-підписникам.

    Parameters
    ----------
    data : list[ProcessedAgentData]
        Пакет оброблених даних агента.

    Returns
    -------
    dict
        Статус виконання операції.
    """
    db_records = []

    for item in data:
        db_records.append(
            {
                "road_state": item.road_state,
                "user_id": item.agent_data.user_id,
                "x": item.agent_data.accelerometer.x,
                "y": item.agent_data.accelerometer.y,
                "z": item.agent_data.accelerometer.z,
                "latitude": item.agent_data.gps.latitude,
                "longitude": item.agent_data.gps.longitude,
                "timestamp": item.agent_data.timestamp,
            }
        )

    with SessionLocal() as db:
        if db_records:
            db.execute(processed_agent_data.insert(), db_records)
            db.commit()

    for record in db_records:
        ws_record = dict(record)
        ws_record["timestamp"] = ws_record["timestamp"].isoformat()
        await send_data_to_subscribers(record["user_id"], ws_record)

    return {"message": "Data successfully processed and saved"}


@app.get(
    "/processed_agent_data/{processed_agent_data_id}",
    response_model=ProcessedAgentDataInDB,
)
def read_processed_agent_data(processed_agent_data_id: int):
    """Повертає один запис processed_agent_data за id."""
    with SessionLocal() as db:
        stmt = processed_agent_data.select().where(
            processed_agent_data.c.id == processed_agent_data_id
        )
        result = db.execute(stmt).first()

        if result is None:
            raise HTTPException(status_code=404, detail="Data not found")

        return result._mapping


@app.get("/processed_agent_data/", response_model=list[ProcessedAgentDataInDB])
def list_processed_agent_data():
    """Повертає список усіх записів processed_agent_data."""
    with SessionLocal() as db:
        stmt = processed_agent_data.select()
        result = db.execute(stmt).all()
        return [row._mapping for row in result]


@app.put(
    "/processed_agent_data/{processed_agent_data_id}",
    response_model=ProcessedAgentDataInDB,
)
def update_processed_agent_data(
    processed_agent_data_id: int,
    data: ProcessedAgentData,
):
    """Оновлює запис processed_agent_data за id."""
    with SessionLocal() as db:
        stmt = (
            processed_agent_data.update()
            .where(processed_agent_data.c.id == processed_agent_data_id)
            .values(
                road_state=data.road_state,
                user_id=data.agent_data.user_id,
                x=data.agent_data.accelerometer.x,
                y=data.agent_data.accelerometer.y,
                z=data.agent_data.accelerometer.z,
                latitude=data.agent_data.gps.latitude,
                longitude=data.agent_data.gps.longitude,
                timestamp=data.agent_data.timestamp,
            )
            .returning(processed_agent_data)
        )

        result = db.execute(stmt).first()

        if result is None:
            raise HTTPException(status_code=404, detail="Data not found")

        db.commit()
        return result._mapping


@app.delete(
    "/processed_agent_data/{processed_agent_data_id}",
    response_model=ProcessedAgentDataInDB,
)
def delete_processed_agent_data(processed_agent_data_id: int):
    """Видаляє запис processed_agent_data за id."""
    with SessionLocal() as db:
        stmt = (
            processed_agent_data.delete()
            .where(processed_agent_data.c.id == processed_agent_data_id)
            .returning(processed_agent_data)
        )

        result = db.execute(stmt).first()

        if result is None:
            raise HTTPException(status_code=404, detail="Data not found")

        db.commit()
        return result._mapping


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)