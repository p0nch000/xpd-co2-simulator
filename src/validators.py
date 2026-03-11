"""Input validation for fuels, fleet, and routes."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from src.constants import ALLOWED_FUEL_UNITS, FLEET_NUMERIC_COLS, FUEL_COLS
from src.utils import (
    clip01,
    demora_sugerida_por_km,
    drop_empty_rows,
    etiqueta_demora,
    parse_horas_demora,
    to_num,
)

# ── Fuels ────────────────────────────────────────────────────────────


def validar_combustibles(df: pd.DataFrame | None) -> pd.DataFrame:
    """Validate and normalize the fuels table."""
    if df is None or df.empty:
        return pd.DataFrame(columns=FUEL_COLS)

    c = drop_empty_rows(df.copy(), "Combustible")

    for col, default in [
        ("Combustible", ""),
        ("Unidad_Consumo", "L"),
    ]:
        if col not in c.columns:
            c[col] = default

    for col in ("Factor_CO2", "Precio_Unitario"):
        if col not in c.columns:
            c[col] = 0.0
        c[col] = to_num(c[col]).fillna(0.0)

    c["Unidad_Consumo"] = c["Unidad_Consumo"].fillna("L").astype(str).str.strip()

    invalid_units = c[~c["Unidad_Consumo"].isin(ALLOWED_FUEL_UNITS)]
    if not invalid_units.empty:
        st.error("Unidad_Consumo inválida. Usa solo 'L', 'kWh' o 'm³'.")
        st.stop()

    return c


# ── Fleet ────────────────────────────────────────────────────────────


def validar_flota(df: pd.DataFrame, label: str) -> pd.DataFrame:
    """Validate fleet composition, checking totals and duplicates."""
    fl = drop_empty_rows(df.copy(), "Unidad")

    # Ensure every expected column exists
    for col in ["Activo", "Unidad", "Combustible"] + FLEET_NUMERIC_COLS:
        if col not in fl.columns:
            fl[col] = np.nan

    fl["Activo"] = fl["Activo"].fillna(False).astype(bool)
    fl["Combustible"] = fl["Combustible"].fillna("").astype(str).str.strip()
    for col in FLEET_NUMERIC_COLS:
        fl[col] = to_num(fl[col]).fillna(0.0).astype(float)

    block_key = f"bloquear_{label}"
    activos = fl[fl["Activo"]].copy()

    if activos.empty:
        st.error(f"{label}: No hay unidades activas.")
        st.session_state[block_key] = True
        return fl

    total_pct = float(activos["Flota %"].sum())
    if abs(total_pct - 100.0) > 0.5:
        st.error(
            f"{label}: La suma de 'Flota %' (solo Activos) es "
            f"{total_pct:.2f}% y debe ser 100%."
        )
        st.session_state[block_key] = True
    else:
        st.session_state[block_key] = False

    bad_yield = activos[
        (activos["Flota %"] > 0)
        & ((activos["Rend_Seco"] <= 0) | (activos["Rend_Refri"] <= 0))
    ]
    if "kWh_por_km" in bad_yield.columns:
        bad_yield = bad_yield[bad_yield["kWh_por_km"] <= 0]

    if not bad_yield.empty:
        st.error(
            f"{label}: Hay unidades activas con % asignado pero "
            "con Rendimiento en 0."
        )
        st.session_state[block_key] = True

    if activos["Unidad"].duplicated(keep=False).any():
        st.error(f"{label}: 'Unidad' duplicada en Activos.")
        st.session_state[block_key] = True

    return fl


# ── Routes ───────────────────────────────────────────────────────────


def normalizar_rutas(df: pd.DataFrame, km_min: float | None) -> pd.DataFrame:
    """Normalize and validate the routes table."""
    ru = drop_empty_rows(df.copy(), "Tramo")

    # Ensure columns
    _defaults: dict[str, object] = {
        "Tramo": "",
        "KM": 0,
        "Viajes": 0,
        "% Refri Local": np.nan,
        "% Urbano": 0.0,
        "Horas_Demora": np.nan,
    }
    for col, default in _defaults.items():
        if col not in ru.columns:
            ru[col] = default

    ru["KM"] = to_num(ru["KM"]).fillna(0.0)
    ru["Viajes"] = to_num(ru["Viajes"]).fillna(0.0)
    ru["% Refri Local"] = to_num(ru["% Refri Local"])
    ru["% Urbano"] = clip01(to_num(ru["% Urbano"]).fillna(0.0))
    ru["Horas_Demora"] = ru["Horas_Demora"].apply(parse_horas_demora)

    # Auto-fill delay from KM where not explicitly set
    auto_mask = ru["Horas_Demora"].isna()
    ru.loc[auto_mask, "Horas_Demora"] = ru.loc[auto_mask, "KM"].apply(
        demora_sugerida_por_km
    )

    # Visual reference column
    ru["Demora_Sugerida"] = (
        ru["KM"].apply(demora_sugerida_por_km).apply(etiqueta_demora)
    )

    if (ru["KM"] < 0).any() or (ru["Viajes"] < 0).any() or (ru["Horas_Demora"] < 0).any():
        st.error("KM, Viajes y Horas_Demora no pueden ser negativos.")
        st.stop()

    # Enforce minimum KM
    if km_min is not None and float(km_min) > 0:
        km_floor = float(km_min)
        ru["KM"] = ru["KM"].clip(lower=km_floor)

        ru["Demora_Sugerida"] = (
            ru["KM"].apply(demora_sugerida_por_km).apply(etiqueta_demora)
        )
        ru.loc[auto_mask, "Horas_Demora"] = ru.loc[auto_mask, "KM"].apply(
            demora_sugerida_por_km
        )

    if not ru.empty and (ru["KM"].sum() == 0 or ru["Viajes"].sum() == 0):
        st.error("Rutas inválidas: suma(KM) y suma(Viajes) deben ser > 0.")
        st.stop()

    # Clip local refrigeration percentages
    refri_mask = ru["% Refri Local"].notna()
    if refri_mask.any():
        ru.loc[refri_mask, "% Refri Local"] = clip01(
            ru.loc[refri_mask, "% Refri Local"]
        )

    return ru
