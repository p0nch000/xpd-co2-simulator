"""JSON persistence layer for the simulator state."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

DATA_DIR = Path.cwd() / "data_app"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SAVE_PATH = DATA_DIR / "estado_emisiones_v2_final.json"


def build_payload(
    flota_a: pd.DataFrame,
    flota_b: pd.DataFrame,
    rutas_a: pd.DataFrame,
    rutas_b: pd.DataFrame,
    combustibles: pd.DataFrame,
) -> dict:
    """Serialize the current working state into a JSON-friendly dict."""
    return {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "flota_A": flota_a.to_dict(orient="records"),
        "flota_B": flota_b.to_dict(orient="records"),
        "rutas_A": rutas_a.to_dict(orient="records"),
        "rutas_B": rutas_b.to_dict(orient="records"),
        "combustibles": combustibles.to_dict(orient="records"),
    }


def write_payload(payload: dict) -> None:
    """Write the payload to disk as JSON."""
    SAVE_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def read_payload() -> dict | None:
    """Read the saved payload from disk, returning *None* on failure."""
    if not SAVE_PATH.exists():
        return None
    try:
        return json.loads(SAVE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None
