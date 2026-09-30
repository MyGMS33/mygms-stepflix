import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DB_PATH = Path(os.getenv("STEPFLIX_DB", str(BASE_DIR / "data" / "stepflix.db")))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="StepFlix", version="0.1.0")


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                duration_minutes REAL NOT NULL CHECK(duration_minutes > 0),
                distance_km REAL NOT NULL CHECK(distance_km >= 0),
                l20_calories REAL,
                steps INTEGER,
                incline_percent REAL NOT NULL DEFAULT 0,
                perceived_effort INTEGER,
                feeling TEXT,
                notes TEXT,
                weight_kg REAL,
                avg_heart_rate INTEGER,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        defaults = {
            "daily_step_goal": 10000,
            "current_weight_kg": None,
            "target_weight_kg": None
        }
        for key, value in defaults.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings(key, value) VALUES(?, ?)",
                (key, json.dumps(value)),
            )
        conn.commit()


init_db()


class SessionIn(BaseModel):
    started_at: str
    duration_minutes: float = Field(gt=0, le=1440)
    distance_km: float = Field(ge=0, le=300)
    l20_calories: Optional[float] = Field(default=None, ge=0, le=20000)
    steps: Optional[int] = Field(default=None, ge=0, le=200000)
    incline_percent: float = Field(default=0, ge=0, le=40)
    perceived_effort: Optional[int] = Field(default=None, ge=1, le=10)
    feeling: Optional[str] = Field(default=None, max_length=40)
    notes: Optional[str] = Field(default=None, max_length=500)
    weight_kg: Optional[float] = Field(default=None, ge=30, le=300)
    avg_heart_rate: Optional[int] = Field(default=None, ge=30, le=240)


class SettingsIn(BaseModel):
    daily_step_goal: Optional[int] = Field(default=None, ge=1000, le=100000)
    current_weight_kg: Optional[float] = Field(default=None, ge=30, le=300)
    target_weight_kg: Optional[float] = Field(default=None, ge=30, le=300)


def get_settings_dict(conn):
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    return {row["key"]: json.loads(row["value"]) for row in rows}


def pace_text(minutes: float, distance: float):
    if distance <= 0:
        return "—"
    pace = minutes / distance
    whole = int(pace)
    seconds = int(round((pace - whole) * 60))
    if seconds == 60:
        whole += 1
        seconds = 0
    return f"{whole}:{seconds:02d} /km"


def estimate_kcal(minutes: float, distance: float, incline: float, weight: Optional[float]):
    if not weight or minutes <= 0 or distance <= 0:
        return None
    speed_kmh = distance / (minutes / 60)
    speed_m_min = speed_kmh * 1000 / 60
    grade = max(0, incline) / 100
    if speed_kmh < 7:
        vo2 = 0.1 * speed_m_min + 1.8 * speed_m_min * grade + 3.5
    else:
        vo2 = 0.2 * speed_m_min + 0.9 * speed_m_min * grade + 3.5
    kcal_min = vo2 * weight / 1000 * 5
    return round(kcal_min * minutes)


def serialize_session(row):
    item = dict(row)
    minutes = float(item["duration_minutes"])
    distance = float(item["distance_km"])
    item["avg_speed_kmh"] = round(distance / (minutes / 60), 2) if minutes else 0
    item["pace"] = pace_text(minutes, distance)
    item["estimated_kcal"] = estimate_kcal(
        minutes, distance, float(item["incline_percent"] or 0), item["weight_kg"]
    )
    return item


@app.get("/api/health")
def health():
    return {"ok": True, "app": "StepFlix"}


@app.get("/api/settings")
def read_settings():
    with connect() as conn:
        return get_settings_dict(conn)


@app.put("/api/settings")
def write_settings(payload: SettingsIn):
    values = payload.model_dump(exclude_unset=True)
    with connect() as conn:
        for key, value in values.items():
            conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value)),
            )
        conn.commit()
        return get_settings_dict(conn)


@app.get("/api/sessions")
def list_sessions(limit: int = 500):
    limit = max(1, min(limit, 5000))
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY started_at DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [serialize_session(row) for row in rows]


@app.post("/api/sessions", status_code=201)
def create_session(payload: SessionIn):
    data = payload.model_dump()
    try:
        datetime.fromisoformat(data["started_at"])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="started_at doit être une date ISO") from exc

    with connect() as conn:
        settings = get_settings_dict(conn)
        if data["weight_kg"] is None:
            data["weight_kg"] = settings.get("current_weight_kg")

        cursor = conn.execute(
            """
            INSERT INTO sessions(
                started_at, duration_minutes, distance_km, l20_calories, steps,
                incline_percent, perceived_effort, feeling, notes, weight_kg,
                avg_heart_rate, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["started_at"],
                data["duration_minutes"],
                data["distance_km"],
                data["l20_calories"],
                data["steps"],
                data["incline_percent"],
                data["perceived_effort"],
                data["feeling"],
                data["notes"],
                data["weight_kg"],
                data["avg_heart_rate"],
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return serialize_session(row)


@app.delete("/api/sessions/{session_id}", status_code=204)
def delete_session(session_id: int):
    with connect() as conn:
        cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Séance introuvable")


@app.get("/api/stats")
def stats():
    with connect() as conn:
        rows = conn.execute("SELECT * FROM sessions ORDER BY started_at ASC").fetchall()
        settings = get_settings_dict(conn)

    sessions = [serialize_session(row) for row in rows]
    now = datetime.now()
    today = now.date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    last_30 = today - timedelta(days=29)

    def date_of(s):
        return datetime.fromisoformat(s["started_at"]).date()

    def sum_for(items):
        total_minutes = sum(float(s["duration_minutes"]) for s in items)
        total_distance = sum(float(s["distance_km"]) for s in items)
        total_steps = sum(int(s["steps"] or 0) for s in items)
        total_l20 = sum(float(s["l20_calories"] or 0) for s in items)
        return {
            "sessions": len(items),
            "minutes": round(total_minutes, 1),
            "distance_km": round(total_distance, 2),
            "steps": total_steps,
            "l20_calories": round(total_l20),
            "avg_speed_kmh": round(total_distance / (total_minutes / 60), 2) if total_minutes else 0,
        }

    this_week = [s for s in sessions if date_of(s) >= week_start]
    this_month = [s for s in sessions if date_of(s) >= month_start]
    rolling_30 = [s for s in sessions if date_of(s) >= last_30]
    today_sessions = [s for s in sessions if date_of(s) == today]

    active_dates = sorted({date_of(s) for s in sessions}, reverse=True)
    streak = 0
    cursor = today
    if active_dates and today not in active_dates:
        cursor = today - timedelta(days=1)
    active_set = set(active_dates)
    while cursor in active_set:
        streak += 1
        cursor -= timedelta(days=1)

    total = sum_for(sessions)
    total["hours"] = round(total["minutes"] / 60, 1)
    return {
        "total": total,
        "week": sum_for(this_week),
        "month": sum_for(this_month),
        "last30": sum_for(rolling_30),
        "today": sum_for(today_sessions),
        "streak_days": streak,
        "daily_step_goal": settings.get("daily_step_goal", 10000),
    }


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
