"""Altair chart builders using the XPD Global brand palette."""

from __future__ import annotations

import altair as alt
import pandas as pd

from src.constants import SCENARIO_COLORS

_CHART_HEIGHT = 360

_COLOR_SCALE = alt.Scale(
    domain=list(SCENARIO_COLORS.keys()),
    range=list(SCENARIO_COLORS.values()),
)


def _scenario_color(field: str = "Escenario:N") -> alt.Color:
    return alt.Color(field, title="Escenario", scale=_COLOR_SCALE)


# ── Chart Builders ───────────────────────────────────────────────────


def bar_co2_by_vehicle(data: pd.DataFrame) -> alt.Chart:
    """Grouped bar chart: CO₂ (tonnes) per vehicle type, A vs B."""
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("Unidad:N", title="Unidad"),
            xOffset="Escenario:N",
            y=alt.Y("tCO2:Q", title="Toneladas de CO₂"),
            color=_scenario_color(),
            tooltip=[
                "Unidad",
                "Escenario",
                alt.Tooltip("CO2_kg:Q", format=",.0f", title="CO₂ (kg)"),
            ],
        )
        .properties(height=_CHART_HEIGHT)
    )


def bar_co2_by_route(data: pd.DataFrame) -> alt.Chart:
    """Grouped bar chart: CO₂ (tonnes) per route, A vs B."""
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("Tramo:N", title="Ruta", sort="-y"),
            xOffset="Escenario:N",
            y=alt.Y("tCO2:Q", title="Toneladas de CO₂"),
            color=_scenario_color(),
            tooltip=[
                "Tramo",
                "Escenario",
                alt.Tooltip("CO2_kg:Q", format=",.0f", title="CO₂ (kg)"),
            ],
        )
        .properties(height=_CHART_HEIGHT)
    )


def donut_participation(data: pd.DataFrame) -> alt.Chart:
    """Donut chart: CO₂ share by vehicle unit for one scenario."""
    return (
        alt.Chart(data)
        .mark_arc(innerRadius=50)
        .encode(
            theta="CO2_kg:Q",
            color=alt.Color("Unidad:N"),
            tooltip=[
                "Unidad",
                alt.Tooltip("CO2_kg:Q", format=",.0f", title="CO₂ (kg)"),
                alt.Tooltip("%_CO2:Q", format=".1f", title="% CO₂"),
            ],
        )
        .properties(height=_CHART_HEIGHT)
    )


def scatter_cost_vs_co2(data: pd.DataFrame) -> alt.Chart:
    """Scatter plot: cost (MXN) vs CO₂ (kg) per unit."""
    return (
        alt.Chart(data)
        .mark_circle(size=140, opacity=0.85)
        .encode(
            x=alt.X("Costo_MXN:Q", title="Costo (MXN)"),
            y=alt.Y("CO2_kg:Q", title="CO₂ (kg)"),
            color=_scenario_color(),
            tooltip=[
                "Unidad",
                "Escenario",
                alt.Tooltip("Costo_MXN:Q", format=",.0f"),
                alt.Tooltip("CO2_kg:Q", format=",.0f"),
            ],
        )
        .properties(height=_CHART_HEIGHT)
    )


def bar_efficiency(data: pd.DataFrame) -> alt.Chart:
    """Grouped bar chart: kg CO₂ / km by vehicle, A vs B."""
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("Unidad:N", title="Unidad"),
            xOffset="Escenario:N",
            y=alt.Y("CO2_kg_por_km:Q", title="kg CO₂ / km"),
            color=_scenario_color(),
            tooltip=[
                "Unidad",
                "Escenario",
                alt.Tooltip("CO2_kg_por_km:Q", format=".4f"),
                alt.Tooltip("Costo_por_km:Q", format=".4f"),
            ],
        )
        .properties(height=_CHART_HEIGHT)
    )
