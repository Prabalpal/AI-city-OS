from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from backend.models.incident import Incident

DB_PATH = Path(__file__).resolve().parent / "incidents.db"


def _get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL
        )
        """
    )
    return connection


def save_incidents_to_db(incidents: dict[str, Incident]) -> None:
    with _get_connection() as connection:
        for incident_id, incident in incidents.items():
            connection.execute(
                "INSERT INTO incidents(id, payload) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET payload = excluded.payload",
                (incident_id, json.dumps(incident.model_dump(mode="json"), ensure_ascii=False)),
            )


def load_persisted_incidents_from_db() -> dict[str, Incident]:
    with _get_connection() as connection:
        rows = connection.execute("SELECT id, payload FROM incidents").fetchall()

    incidents: dict[str, Incident] = {}
    for row in rows:
        payload = json.loads(row["payload"])
        incidents[row["id"]] = Incident.model_validate(payload)
    return incidents


def clear_incidents_db() -> None:
    with _get_connection() as connection:
        connection.execute("DELETE FROM incidents")
