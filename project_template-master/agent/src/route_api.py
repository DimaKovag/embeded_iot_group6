from __future__ import annotations

import csv
import random
from pathlib import Path
from typing import List, Tuple

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
GPS_CSV = DATA_DIR / "gps.csv"
ACCEL_CSV = DATA_DIR / "accelerometer.csv"
PARKING_CSV = DATA_DIR / "parking.csv"

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

app = FastAPI(title="Route generator API")


class Point(BaseModel):
    """Точка маршруту у форматі довгота/широта."""
    longitude: float = Field(..., description="Longitude")
    latitude: float = Field(..., description="Latitude")


class RouteRequest(BaseModel):
    """Параметри генерації маршруту та синтетичних сенсорних даних."""
    start: Point
    end: Point
    round_trip: bool = True
    step: int = Field(1, ge=1, description="Take every Nth GPS point from route")
    base_z: int = 8
    bump_z: int = 14
    pothole_z: int = 20
    bump_every: int = 25
    pothole_every: int = 80
    noise_xy: int = 1
    parking_empty_count: int = 20


def fetch_route_points(start: Point, end: Point) -> List[Tuple[float, float]]:
    """Отримує маршрут між двома точками через OSRM.

    Parameters
    ----------
    start : Point
        Початкова точка.
    end : Point
        Кінцева точка.

    Returns
    -------
    list[tuple[float, float]]
        Список координат у форматі ``(longitude, latitude)``.
    """
    url = (
        f"{OSRM_URL}/"
        f"{start.longitude},{start.latitude};"
        f"{end.longitude},{end.latitude}"
        f"?overview=full&geometries=geojson"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    payload = response.json()
    routes = payload.get("routes", [])
    if not routes:
        raise HTTPException(status_code=400, detail="OSRM did not return a route")

    coordinates = routes[0]["geometry"]["coordinates"]
    return [(lon, lat) for lon, lat in coordinates]


def downsample(points: List[Tuple[float, float]], step: int) -> List[Tuple[float, float]]:
    """Проріджує список GPS-точок.

    Parameters
    ----------
    points : list[tuple[float, float]]
        Вхідний список точок.
    step : int
        Крок вибірки.

    Returns
    -------
    list[tuple[float, float]]
        Проріджений список точок.
    """
    if not points:
        return []

    sampled = points[::step]
    if sampled[-1] != points[-1]:
        sampled.append(points[-1])
    return sampled


def build_round_trip(points: List[Tuple[float, float]], round_trip: bool) -> List[Tuple[float, float]]:
    """Формує маршрут туди-назад."""
    if not round_trip or len(points) < 2:
        return points
    return points + points[-2::-1]


def generate_accelerometer_data(
    count: int,
    base_z: int,
    bump_z: int,
    pothole_z: int,
    bump_every: int,
    pothole_every: int,
    noise_xy: int,
) -> List[Tuple[int, int, int]]:
    """Генерує синтетичні дані акселерометра.

    Parameters
    ----------
    count : int
        Кількість рядків.
    base_z : int
        Базове значення осі Z.
    bump_z : int
        Значення Z для нерівності.
    pothole_z : int
        Значення Z для ями.
    bump_every : int
        Частота вставки bump.
    pothole_every : int
        Частота вставки pothole.
    noise_xy : int
        Межа випадкового шуму для X та Y.

    Returns
    -------
    list[tuple[int, int, int]]
        Список рядків акселерометра у форматі ``(x, y, z)``.
    """
    result: List[Tuple[int, int, int]] = []

    for i in range(count):
        x = random.randint(-noise_xy, noise_xy)
        y = random.randint(-noise_xy, noise_xy)
        z = base_z + random.randint(-1, 1)

        if pothole_every > 0 and i > 0 and i % pothole_every == 0:
            z = pothole_z + random.randint(-1, 1)
        elif bump_every > 0 and i > 0 and i % bump_every == 0:
            z = bump_z + random.randint(-1, 1)

        result.append((x, y, z))

    return result


def write_gps_csv(points: List[Tuple[float, float]], filename: Path) -> None:
    """Записує GPS-точки у CSV."""
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["longitude", "latitude"])
        writer.writerows(points)


def write_accelerometer_csv(rows: List[Tuple[int, int, int]], filename: Path) -> None:
    """Записує дані акселерометра у CSV."""
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["x", "y", "z"])
        writer.writerows(rows)


def write_parking_csv(
    points: List[Tuple[float, float]],
    filename: Path,
    empty_count: int,
) -> None:
    """Записує дані паркування у CSV."""
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["empty_count", "latitude", "longitude"])
        for lon, lat in points:
            writer.writerow([empty_count, lat, lon])


@app.get("/health")
def health() -> dict:
    """Перевірка доступності API."""
    return {"status": "ok"}


@app.post("/generate")
def generate_route(request: RouteRequest) -> dict:
    """Генерує CSV-файли маршруту та сенсорних даних."""
    try:
        raw_points = fetch_route_points(request.start, request.end)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"OSRM request failed: {e}") from e

    if len(raw_points) < 2:
        raise HTTPException(status_code=400, detail="Too few route points returned")

    gps_points = downsample(raw_points, request.step)
    gps_points = build_round_trip(gps_points, request.round_trip)

    accel_rows = generate_accelerometer_data(
        count=len(gps_points),
        base_z=request.base_z,
        bump_z=request.bump_z,
        pothole_z=request.pothole_z,
        bump_every=request.bump_every,
        pothole_every=request.pothole_every,
        noise_xy=request.noise_xy,
    )

    write_gps_csv(gps_points, GPS_CSV)
    write_accelerometer_csv(accel_rows, ACCEL_CSV)
    write_parking_csv(gps_points, PARKING_CSV, request.parking_empty_count)

    return {
        "status": "ok",
        "gps_points_written": len(gps_points),
        "accelerometer_rows_written": len(accel_rows),
        "parking_rows_written": len(gps_points),
        "gps_csv": str(GPS_CSV),
        "accelerometer_csv": str(ACCEL_CSV),
        "parking_csv": str(PARKING_CSV),
    }