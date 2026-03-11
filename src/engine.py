"""CO₂ emission calculation engine and summary builders."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.constants import (
    MAX_URBAN_PENALTY_RATIO,
    MAX_WEIGHT_BONUS_PCT,
    MIN_EFFECTIVE_LOAD_FACTOR,
    MIN_EFFECTIVE_URBAN_FACTOR,
)
from src.utils import to_num
from src.validators import validar_combustibles

# ── Calculation Engine ───────────────────────────────────────────────


def motor_detallado_v2(
    flota: pd.DataFrame,
    rutas: pd.DataFrame,
    comb_df: pd.DataFrame,
    penal_urbana_pct: float,
    pct_llenado_global: float,
    solo_refri: bool = False,
) -> pd.DataFrame:
    """Run the detailed emission model across all route×vehicle combinations."""
    comb_df = validar_combustibles(comb_df)
    comb_map = {row["Combustible"]: row for _, row in comb_df.iterrows()}

    activos = flota[flota["Activo"] == True].copy()  # noqa: E712
    activos["Flota %"] = to_num(activos["Flota %"]).fillna(0.0)

    weight_bonus = MAX_WEIGHT_BONUS_PCT * (1.0 - pct_llenado_global / 100.0)

    rows: list[dict] = []
    for _, route in rutas.iterrows():
        km = float(route["KM"])
        trips = float(route["Viajes"])
        total_dist = km * trips

        urban_ratio = max(0.0, min(1.0, float(route["% Urbano"]) / 100.0))
        penalty = max(0.0, min(MAX_URBAN_PENALTY_RATIO, penal_urbana_pct / 100.0))
        urban_factor = 1.0 - penalty * urban_ratio
        load_factor = 1.0 + weight_bonus

        delay_hours = max(0.0, float(route["Horas_Demora"]))
        has_local_refri = pd.notna(route["% Refri Local"])
        local_refri_pct = float(route["% Refri Local"]) if has_local_refri else None

        for _, vehicle in activos.iterrows():
            unit_name = str(vehicle["Unidad"])
            fuel_name = str(vehicle["Combustible"]).strip()
            if fuel_name not in comb_map:
                continue

            fuel_info = comb_map[fuel_name]
            consumption_unit = str(fuel_info.get("Unidad_Consumo", "L"))
            co2_factor = float(fuel_info.get("Factor_CO2", 0.0))
            unit_price = float(fuel_info.get("Precio_Unitario", 0.0))

            fleet_share = float(vehicle["Flota %"]) / 100.0
            vehicle_trips = trips * fleet_share
            vehicle_km = total_dist * fleet_share

            refri_pct = (
                local_refri_pct
                if has_local_refri
                else float(vehicle.get("Refri Global %", 0.0))
            )
            refri_pct = max(0.0, min(100.0, refri_pct))
            km_refri = vehicle_km * (refri_pct / 100.0)
            km_seco = vehicle_km - km_refri

            route_consumption = _calc_route_consumption(
                vehicle, consumption_unit, km_seco, km_refri,
                urban_factor, load_factor,
            )
            if route_consumption is None:
                continue

            idle_rate = float(vehicle.get("L/hr_Ralenti", 0.0))
            idle_consumption = vehicle_trips * delay_hours * max(0.0, idle_rate)
            total_consumption = route_consumption + idle_consumption

            if solo_refri and total_consumption <= 0:
                continue

            rows.append({
                "Tramo": route["Tramo"],
                "Unidad": unit_name,
                "Combustible": fuel_name,
                "Unidad_Consumo": consumption_unit,
                "Viajes_V": vehicle_trips,
                "KM_V": vehicle_km,
                "Consumo_Ruta": route_consumption,
                "Consumo_Ralenti": idle_consumption,
                "Consumo_Total": total_consumption,
                "CO2_kg": total_consumption * co2_factor,
                "Costo_MXN": total_consumption * unit_price,
            })

    result = pd.DataFrame(rows)
    if not result.empty:
        result["CO2_kg_por_km"] = np.where(
            result["KM_V"] > 0, result["CO2_kg"] / result["KM_V"], 0.0
        )
        result["CO2_kg_por_viaje"] = np.where(
            result["Viajes_V"] > 0, result["CO2_kg"] / result["Viajes_V"], 0.0
        )
        result["Costo_por_km"] = np.where(
            result["KM_V"] > 0, result["Costo_MXN"] / result["KM_V"], 0.0
        )
        result["Costo_por_viaje"] = np.where(
            result["Viajes_V"] > 0, result["Costo_MXN"] / result["Viajes_V"], 0.0
        )
    return result


def _calc_route_consumption(
    vehicle: pd.Series,
    unit: str,
    km_seco: float,
    km_refri: float,
    urban_factor: float,
    load_factor: float,
) -> float | None:
    """Calculate route fuel/energy consumption for a single vehicle."""
    if unit == "kWh":
        kwh_km = float(vehicle.get("kWh_por_km", 0.0))
        kwh_km_refri = float(vehicle.get("kWh_por_km_refri", 0.0))
        if kwh_km <= 0:
            return None
        if kwh_km_refri <= 0:
            kwh_km_refri = kwh_km
        base = km_seco * kwh_km + km_refri * kwh_km_refri
        return base * (
            1.0 / max(MIN_EFFECTIVE_URBAN_FACTOR, urban_factor)
        ) * (
            1.0 / max(MIN_EFFECTIVE_LOAD_FACTOR, load_factor)
        )

    # Volumetric fuel (L or m³)
    rs = float(vehicle.get("Rend_Seco", 0.0))
    rr = float(vehicle.get("Rend_Refri", 0.0))
    if rs <= 0 or rr <= 0:
        return None
    rs_eff = rs * urban_factor * load_factor
    rr_eff = rr * urban_factor * load_factor
    return (
        (km_seco / rs_eff if rs_eff > 0 else 0.0)
        + (km_refri / rr_eff if rr_eff > 0 else 0.0)
    )


# ── Summaries ────────────────────────────────────────────────────────

_SUM_COLS = ["Viajes_V", "KM_V", "Consumo_Total", "CO2_kg", "Costo_MXN"]


def _add_intensity_cols(df: pd.DataFrame, km_col: str = "KM_V") -> pd.DataFrame:
    """Add per-km / per-trip intensity columns."""
    dist = km_col if km_col in df.columns else "Distancia_km"
    df["CO2_kg_por_km"] = np.where(df[dist] > 0, df["CO2_kg"] / df[dist], 0.0)
    df["CO2_kg_por_viaje"] = np.where(df["Viajes_V"] > 0, df["CO2_kg"] / df["Viajes_V"], 0.0)
    df["Costo_por_km"] = np.where(df[dist] > 0, df["Costo_MXN"] / df[dist], 0.0)
    df["Costo_por_viaje"] = np.where(df["Viajes_V"] > 0, df["Costo_MXN"] / df["Viajes_V"], 0.0)
    return df


def resumen_por_unidad(det: pd.DataFrame) -> pd.DataFrame:
    """Summarize emissions by vehicle unit."""
    if det.empty:
        return pd.DataFrame()

    res = (
        det.groupby(["Unidad", "Combustible", "Unidad_Consumo"], as_index=False)[_SUM_COLS]
        .sum()
        .rename(columns={"KM_V": "Distancia_km"})
    )
    total_co2 = float(res["CO2_kg"].sum())
    total_cost = float(res["Costo_MXN"].sum())
    res["%_CO2"] = np.where(total_co2 > 0, 100 * res["CO2_kg"] / total_co2, 0.0)
    res["%_Costo"] = np.where(total_cost > 0, 100 * res["Costo_MXN"] / total_cost, 0.0)

    return _add_intensity_cols(res).sort_values("CO2_kg", ascending=False)


def resumen_por_ruta(det: pd.DataFrame) -> pd.DataFrame:
    """Summarize emissions by route segment."""
    if det.empty:
        return pd.DataFrame()

    rr = det.groupby("Tramo", as_index=False)[_SUM_COLS].sum()
    total_co2 = float(rr["CO2_kg"].sum())
    rr["%_CO2"] = np.where(total_co2 > 0, 100 * rr["CO2_kg"] / total_co2, 0.0)

    return _add_intensity_cols(rr).sort_values("CO2_kg", ascending=False)


def top3(df: pd.DataFrame | None, col: str = "CO2_kg") -> pd.DataFrame:
    """Return the 3 highest-emitting rows."""
    if df is None or df.empty:
        return pd.DataFrame()
    return df.nlargest(3, col)
