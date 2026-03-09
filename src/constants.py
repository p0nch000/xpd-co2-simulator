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
    "Activo": [True, True, True, True, True, True, False],
    "Unidad": [
        "1.5 T", "3.5 T (Gas)", "3.5 T (Die)",
        "RABON", "CAJA 53", "EV Van", "Automóvil",
    ],
    "Combustible": [
        "Gasolina", "Gasolina", "Diesel",
        "Diesel", "Diesel", "Eléctrico", "Gasolina",
    ],
    "Flota %": [25.0, 15.0, 20.0, 20.0, 20.0, 0.0, 0.0],
    "Rend_Seco": [8.0, 5.5, 6.5, 3.5, 1.8, 0.0, 12.0],
    "Rend_Refri": [6.8, 4.8, 5.5, 3.0, 1.5, 0.0, 12.0],
    "Refri Global %": [4.0, 0.0, 0.0, 0.0, 10.0, 0.0, 0.0],
    "L/hr_Ralenti": [0.6, 1.0, 1.2, 2.0, 3.5, 1.5, 0.4],
    "kWh_por_km": [0.0, 0.0, 0.0, 0.0, 0.0, 0.28, 0.0],
    "kWh_por_km_refri": [0.0, 0.0, 0.0, 0.0, 0.0, 0.34, 0.0],
})

DEFAULT_ROUTES = pd.DataFrame([
    {
        "Tramo": "Guadalajara - Puebla",
        "KM": 671, "Viajes": 1465,
        "% Refri Local": np.nan, "% Urbano": 10, "Horas_Demora": 3,
    },
    {
        "Tramo": "CDMX - Tlaxcala",
        "KM": 118, "Viajes": 2307,
        "% Refri Local": np.nan, "% Urbano": 70, "Horas_Demora": 4,
    },
    {
        "Tramo": "Guadalajara - Irapuato",
        "KM": 250, "Viajes": 50,
        "% Refri Local": 100, "% Urbano": 20, "Horas_Demora": 6,
    },
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
