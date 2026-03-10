"""
Centralized constants for the XPD CO₂ Logistics Simulator.

All magic numbers, brand palette, default datasets, and threshold
values live here so the rest of the codebase stays clean.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ── XPD Brand Palette ────────────────────────────────────────────────
XPD_BLUE = "#0561FC"
XPD_ORANGE = "#FE5229"
XPD_NAVY = "#171E34"
XPD_LIGHT_GRAY = "#F7F7F7"
XPD_WHITE = "#FFFFFF"

SCENARIO_COLORS: dict[str, str] = {
    "CO2_A": XPD_BLUE,
    "CO2_B": XPD_ORANGE,
    "A": XPD_BLUE,
    "B": XPD_ORANGE,
}

# ── Delay Thresholds (km → hours) ───────────────────────────────────
DELAY_THRESHOLDS: list[tuple[float, float]] = [
    (50, 0.25),    # ≤ 50 km  → 15 min
    (200, 0.50),   # ≤ 200 km → 30 min
    (500, 1.00),   # ≤ 500 km → 1 h
]
DELAY_DEFAULT_HOURS = 2.00  # > 500 km

# ── Logistics Defaults ──────────────────────────────────────────────
MAX_WEIGHT_BONUS_PCT = 0.25        # up to 25 % fuel savings when empty
MAX_URBAN_PENALTY_RATIO = 0.79     # cap for urban penalty factor
MIN_EFFECTIVE_URBAN_FACTOR = 0.05
MIN_EFFECTIVE_LOAD_FACTOR = 0.70

# ── Allowed fuel consumption units ──────────────────────────────────
ALLOWED_FUEL_UNITS: set[str] = {"L", "kWh"}

# ── Default DataFrames ──────────────────────────────────────────────
DEFAULT_FUELS = pd.DataFrame({
    "Combustible": ["Gasolina", "Diesel", "Eléctrico", "GNC"],
    "Unidad_Consumo": ["L", "L", "kWh", "L"],
    "Factor_CO2": [2.31, 2.68, 0.435, 2.02],
    "Precio_Unitario": [23.27, 26.28, 3.50, 11.50],
})

DEFAULT_FLEET = pd.DataFrame({
    "Activo": [True, True, True, True, True, False, True, True],
    "Unidad": [
        "1.5 T", "3.5 T (Gas)", "3.5 T (Die)",
        "RABON", "CAJA 53", "EV Van", "Torton", "Automóvil",
    ],
    "Combustible": [
        "Gasolina", "Gasolina", "Diesel",
        "Diesel", "Diesel", "Eléctrico", "Diesel", "Gasolina",
    ],
    "Flota %": [10.0, 7.5, 7.5, 25.0, 35.0, 0.0, 10.0, 5.0],
    "Rend_Seco": [7.0, 3.5, 5.5, 3.2, 1.8, 0.0, 2.4, 14.0],
    "Rend_Refri": [5.6, 2.4, 4.4, 2.4, 1.2, 1.0, 1.6, 14.0],
    "Refri Global %": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "L/hr_Ralenti": [5.6, 0.7, 1.1, 2.0, 3.5, 0.0, 2.6, 0.5],
    "kWh_por_km": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "kWh_por_km_refri": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
})

DEFAULT_ROUTES = pd.DataFrame([
    {"Tramo": "Guadalajara - Puebla", "KM": 671, "Viajes": 1465, "% Refri Local": np.nan, "% Urbano": 0, "Horas_Demora": np.nan},
    {"Tramo": "Ciudad De México, MEX - Tlaxcala", "KM": 118, "Viajes": 2307, "% Refri Local": np.nan, "% Urbano": 0, "Horas_Demora": np.nan},
    {"Tramo": "Toluca - Puebla", "KM": 191, "Viajes": 1493, "% Refri Local": np.nan, "% Urbano": 0, "Horas_Demora": np.nan},
    {"Tramo": "Queretaro, MEX - Tlaxcala", "KM": 310, "Viajes": 904, "% Refri Local": np.nan, "% Urbano": 0, "Horas_Demora": np.nan},
    {"Tramo": "San Luis Potosí, MEX - San Luis Potosí, MEX", "KM": 0, "Viajes": 658, "% Refri Local": np.nan, "% Urbano": 0, "Horas_Demora": np.nan},
    {"Tramo": "Uruapan, MEX - San Luis Potosí, MEX", "KM": 400, "Viajes": 614, "% Refri Local": np.nan, "% Urbano": 0, "Horas_Demora": np.nan},
    {"Tramo": "Ciudad Juarez, MEX - Toluca", "KM": 1777, "Viajes": 575, "% Refri Local": np.nan, "% Urbano": 0, "Horas_Demora": np.nan},
    {"Tramo": "Queretaro - Puebla, MEX", "KM": 330, "Viajes": 515, "% Refri Local": np.nan, "% Urbano": 0, "Horas_Demora": np.nan},
    {"Tramo": "Queretaro, MEX - Aguascalientes, MEX", "KM": 200, "Viajes": 507, "% Refri Local": np.nan, "% Urbano": 0, "Horas_Demora": np.nan},
    {"Tramo": "Tlaxcala, MEX - Ciudad De México, MEX", "KM": 118, "Viajes": 485, "% Refri Local": np.nan, "% Urbano": 0, "Horas_Demora": np.nan},
])

# ── Fleet / Route Column Specs ──────────────────────────────────────
FLEET_NUMERIC_COLS = [
    "Flota %", "Rend_Seco", "Rend_Refri",
    "Refri Global %", "L/hr_Ralenti",
    "kWh_por_km", "kWh_por_km_refri",
]

FLEET_ALL_COLS = [
    "Activo", "Unidad", "Combustible", "Flota %",
    "Rend_Seco", "Rend_Refri", "Refri Global %",
    "L/hr_Ralenti", "kWh_por_km", "kWh_por_km_refri",
]

FUEL_COLS = ["Combustible", "Unidad_Consumo", "Factor_CO2", "Precio_Unitario"]
