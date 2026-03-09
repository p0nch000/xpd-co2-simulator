"""Pure utility functions — no Streamlit dependency."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from src.constants import DELAY_DEFAULT_HOURS, DELAY_THRESHOLDS

# ── Numeric helpers ──────────────────────────────────────────────────


def to_num(series: pd.Series) -> pd.Series:
    """Coerce a Series to numeric, replacing failures with NaN."""
    return pd.to_numeric(series, errors="coerce")


def clip01(series: pd.Series) -> pd.Series:
    """Clip values to the [0, 100] range."""
    return series.clip(0, 100)


# ── DataFrame helpers ────────────────────────────────────────────────


def df_hash(df: pd.DataFrame | None) -> str:
    """Deterministic hash of a DataFrame for cheap equality checks."""
    if df is None or df.empty:
        return "EMPTY"
    normalized = df.reindex(sorted(df.columns), axis=1).reset_index(drop=True)
    return str(int(pd.util.hash_pandas_object(normalized, index=False).sum()))


def records_to_df(records: list[dict] | None) -> pd.DataFrame:
    """Safely convert a list of dicts to a DataFrame."""
    return pd.DataFrame(records) if isinstance(records, list) else pd.DataFrame()


def drop_empty_rows(df: pd.DataFrame, key_col: str) -> pd.DataFrame:
    """Drop fully-NaN rows and rows where *key_col* is blank/NaN."""
    df = df.dropna(how="all")
    if key_col in df.columns:
        df[key_col] = df[key_col].astype(str).str.strip()
        df = df[~df[key_col].isin({"", "None", "nan"})]
    return df


# ── Delay / Demora helpers ───────────────────────────────────────────

_DEMORA_TEXT_MAP: dict[str, float] = {
    "15 min": 0.25,
    "30 min": 0.50,
    "1 hora": 1.00,
    "2 horas": 2.00,
    "1 hr": 1.00,
    "2 hrs": 2.00,
    "1 h": 1.00,
    "2 h": 2.00,
}

_DEMORA_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(min|mins|minuto|minutos|h|hr|hrs|hora|horas)\s*$"
)


def demora_sugerida_por_km(km: float) -> float:
    """Return suggested delay (hours) based on route distance."""
    try:
        km = float(km)
    except (TypeError, ValueError):
        return 0.0

    for threshold_km, hours in DELAY_THRESHOLDS:
        if km <= threshold_km:
            return hours
    return DELAY_DEFAULT_HOURS


def parse_horas_demora(value: object) -> float:
    """Parse a delay value that may be numeric or a text label like '15 min'."""
    if pd.isna(value):
        return np.nan

    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)

    text = str(value).strip().lower()
    if text == "":
        return np.nan

    if text in _DEMORA_TEXT_MAP:
        return _DEMORA_TEXT_MAP[text]

    match = _DEMORA_RE.match(text)
    if match:
        number = float(match.group(1))
        unit = match.group(2)
        return number / 60.0 if unit.startswith("min") else number

    try:
        return float(text)
    except (TypeError, ValueError):
        return np.nan


def etiqueta_demora(hours: float) -> str:
    """Human-readable label for a delay value in hours."""
    try:
        h = float(hours)
    except (TypeError, ValueError):
        return ""

    _LABELS: dict[float, str] = {0.25: "15 min", 0.50: "30 min", 1.00: "1 hora", 2.00: "2 horas"}
    for ref, label in _LABELS.items():
        if abs(h - ref) < 1e-9:
            return label
    return f"{int(round(h * 60))} min" if h < 1 else f"{h:g} h"
