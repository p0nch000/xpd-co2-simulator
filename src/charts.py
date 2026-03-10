"""Altair chart builders — executive-grade visuals for XPD Global."""

from __future__ import annotations

import altair as alt
import pandas as pd

from src.constants import SCENARIO_COLORS, XPD_BLUE, XPD_NAVY, XPD_ORANGE

# ── Theme Constants ─────────────────────────────────────────────────
_FONT = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
_LABEL_COLOR = "#555"
_GRID_COLOR = "#e8ecf1"
_AXIS_COLOR = "#ccd2da"

_COLOR_SCALE = alt.Scale(
    domain=list(SCENARIO_COLORS.keys()),
    range=list(SCENARIO_COLORS.values()),
)

_SCENARIO_LEGEND = alt.Legend(
    title="Escenario",
    orient="top-right",
    titleFontSize=12,
    titleFont=_FONT,
    titleColor=XPD_NAVY,
    labelFont=_FONT,
    labelFontSize=12,
    labelColor=_LABEL_COLOR,
    symbolSize=120,
    symbolStrokeWidth=0,
    padding=10,
    cornerRadius=6,
)


def _scenario_color(field: str = "Escenario:N") -> alt.Color:
    return alt.Color(field, scale=_COLOR_SCALE, legend=_SCENARIO_LEGEND)


def _theme(chart: alt.Chart, title: str = "", height: int = 520) -> alt.Chart:
    """Apply XPD executive theme."""
    c = chart.properties(
        height=height,
        title=alt.Title(
            title, font=_FONT, fontSize=16, fontWeight=700,
            color=XPD_NAVY, anchor="start", offset=16,
        ) if title else alt.Undefined,
    )
    return (
        c
        .configure(
            font=_FONT,
            padding={"left": 24, "right": 24, "top": 20, "bottom": 20},
        )
        .configure_axis(
            gridColor=_GRID_COLOR,
            gridDash=[3, 3],
            domainColor=_AXIS_COLOR,
            tickColor=_AXIS_COLOR,
            labelColor=_LABEL_COLOR,
            titleColor=XPD_NAVY,
            labelFontSize=12,
            titleFontSize=13,
            titleFont=_FONT,
            labelFont=_FONT,
            titlePadding=12,
            labelPadding=8,
        )
        .configure_legend(
            labelFont=_FONT,
            titleFont=_FONT,
            labelColor=_LABEL_COLOR,
            titleColor=XPD_NAVY,
        )
        .configure_view(strokeWidth=0)
        .configure_title(font=_FONT)
    )


# ── 1. Comparativa CO₂ por Vehículo (A vs B) ─────────────────────


def bar_co2_by_vehicle(data: pd.DataFrame) -> alt.Chart:
    """Grouped bar chart: tCO₂ per vehicle, A vs B."""
    bars = (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, opacity=0.92)
        .encode(
            x=alt.X("Unidad:N", title=None, axis=alt.Axis(labelAngle=-30, labelFontSize=12)),
            xOffset="Escenario:N",
            y=alt.Y("tCO2:Q", title="Toneladas CO₂",
                     axis=alt.Axis(format=",.1f", grid=True)),
            color=_scenario_color(),
            tooltip=[
                alt.Tooltip("Unidad:N", title="Vehículo"),
                alt.Tooltip("Escenario:N"),
                alt.Tooltip("tCO2:Q", format=",.2f", title="tCO₂"),
            ],
        )
    )
    labels = (
        alt.Chart(data)
        .mark_text(dy=-12, fontSize=11, fontWeight=700, font=_FONT, color=XPD_NAVY)
        .encode(
            x=alt.X("Unidad:N"),
            xOffset="Escenario:N",
            y=alt.Y("tCO2:Q"),
            text=alt.Text("tCO2:Q", format=",.1f"),
        )
    )
    return _theme(bars + labels, "Comparativa CO₂ por Tipo de Vehículo")


# ── 2. CO₂ por Ruta (Top 15) ────────────────────────────────────


def bar_co2_by_route(data: pd.DataFrame) -> alt.Chart:
    """Horizontal bar chart: CO₂ by route, top 15, sorted descending."""
    if not data.empty and "Tramo" in data.columns:
        top = (
            data.groupby("Tramo", as_index=False)["tCO2"]
            .sum()
            .nlargest(15, "tCO2")["Tramo"]
            .tolist()
        )
        data = data[data["Tramo"].isin(top)].copy()

    bars = (
        alt.Chart(data)
        .mark_bar(cornerRadiusEnd=5, opacity=0.92)
        .encode(
            y=alt.Y("Tramo:N", title=None, sort="-x",
                     axis=alt.Axis(labelLimit=300, labelFontSize=11)),
            yOffset="Escenario:N",
            x=alt.X("tCO2:Q", title="Toneladas CO₂",
                     axis=alt.Axis(format=",.1f", grid=True)),
            color=_scenario_color(),
            tooltip=[
                alt.Tooltip("Tramo:N", title="Ruta"),
                alt.Tooltip("Escenario:N"),
                alt.Tooltip("tCO2:Q", format=",.2f", title="tCO₂"),
            ],
        )
    )
    n_routes = len(data["Tramo"].unique()) if not data.empty else 1
    h = max(520, n_routes * 36)
    return _theme(bars, "Top Rutas — Emisiones CO₂", height=h)


# ── 3. Participación por Unidad (Donut) ───────────────────────────


def donut_participation(data: pd.DataFrame) -> alt.Chart:
    """Donut chart — labels OUTSIDE the arcs to prevent overlap."""
    _INNER = 80
    _OUTER = 170
    _LABEL_RADIUS = _OUTER + 30  # labels live outside the ring

    data = data.copy()
    data["_label"] = data.apply(
        lambda r: f"{r['Unidad']}: {r['%_CO2']:.1f}%" if r["%_CO2"] >= 2.0 else "",
        axis=1,
    )

    base = alt.Chart(data)

    arcs = (
        base
        .mark_arc(innerRadius=_INNER, outerRadius=_OUTER, stroke="#fff", strokeWidth=3)
        .encode(
            theta=alt.Theta("CO2_kg:Q", stack=True),
            color=alt.Color(
                "Unidad:N",
                legend=alt.Legend(
                    title="Unidad", orient="bottom", columns=4,
                    titleFont=_FONT, titleColor=XPD_NAVY,
                    labelFont=_FONT, labelColor=_LABEL_COLOR,
                    labelFontSize=12, symbolSize=140, rowPadding=6,
                ),
            ),
            order=alt.Order("CO2_kg:Q", sort="descending"),
            tooltip=[
                alt.Tooltip("Unidad:N"),
                alt.Tooltip("CO2_kg:Q", format=",.0f", title="CO₂ (kg)"),
                alt.Tooltip("%_CO2:Q", format=".1f", title="% CO₂"),
            ],
        )
    )

    outer_labels = (
        base
        .mark_text(radius=_LABEL_RADIUS, fontSize=12, fontWeight=700, font=_FONT)
        .encode(
            theta=alt.Theta("CO2_kg:Q", stack=True),
            order=alt.Order("CO2_kg:Q", sort="descending"),
            text="_label:N",
            color=alt.value(XPD_NAVY),
        )
    )

    return _theme(arcs + outer_labels, "Distribución de Emisiones por Unidad", height=520)


# ── 4. Costo vs CO₂ (Scatter + Trend) ────────────────────────────


def scatter_cost_vs_co2(data: pd.DataFrame) -> alt.Chart:
    """Scatter plot with bubbles sized by CO₂ and regression line."""
    points = (
        alt.Chart(data)
        .mark_circle(opacity=0.8, strokeWidth=2, stroke="#fff")
        .encode(
            x=alt.X("Costo_MXN:Q", title="Costo Operativo (MXN)",
                     axis=alt.Axis(format="$,.0f", grid=True)),
            y=alt.Y("CO2_kg:Q", title="Emisiones CO₂ (kg)",
                     axis=alt.Axis(format=",.0f", grid=True)),
            color=_scenario_color(),
            size=alt.Size("CO2_kg:Q", legend=None,
                          scale=alt.Scale(range=[120, 900])),
            tooltip=[
                alt.Tooltip("Unidad:N", title="Vehículo"),
                alt.Tooltip("Escenario:N"),
                alt.Tooltip("Costo_MXN:Q", format="$,.0f", title="Costo"),
                alt.Tooltip("CO2_kg:Q", format=",.0f", title="CO₂ (kg)"),
            ],
        )
    )

    labels = (
        alt.Chart(data)
        .mark_text(dy=-18, fontSize=11, fontWeight=600, font=_FONT)
        .encode(
            x="Costo_MXN:Q",
            y="CO2_kg:Q",
            text="Unidad:N",
            color=alt.value(XPD_NAVY),
        )
    )

    reg = (
        alt.Chart(data)
        .transform_regression("Costo_MXN", "CO2_kg")
        .mark_line(strokeDash=[6, 4], strokeWidth=2, opacity=0.4)
        .encode(
            x="Costo_MXN:Q",
            y="CO2_kg:Q",
            color=alt.value("#999"),
        )
    )

    return _theme(points + labels + reg, "Relación Costo vs Emisiones CO₂")


# ── 5. Eficiencia Ambiental ───────────────────────────────────────


def bar_efficiency(data: pd.DataFrame) -> alt.Chart:
    """Horizontal grouped bar: kg CO₂/km per unit, A vs B."""
    bars = (
        alt.Chart(data)
        .mark_bar(cornerRadiusEnd=5, opacity=0.92)
        .encode(
            y=alt.Y("Unidad:N", title=None, axis=alt.Axis(labelFontSize=12)),
            yOffset="Escenario:N",
            x=alt.X("CO2_kg_por_km:Q", title="kg CO₂ / km",
                     axis=alt.Axis(format=".3f", grid=True)),
            color=_scenario_color(),
            tooltip=[
                alt.Tooltip("Unidad:N", title="Vehículo"),
                alt.Tooltip("Escenario:N"),
                alt.Tooltip("CO2_kg_por_km:Q", format=".4f", title="kg CO₂/km"),
                alt.Tooltip("Costo_por_km:Q", format="$,.4f", title="$/km"),
            ],
        )
    )

    labels = (
        alt.Chart(data)
        .mark_text(dx=4, align="left", fontSize=11, fontWeight=700, font=_FONT, color=XPD_NAVY)
        .encode(
            y=alt.Y("Unidad:N"),
            yOffset="Escenario:N",
            x=alt.X("CO2_kg_por_km:Q"),
            text=alt.Text("CO2_kg_por_km:Q", format=".3f"),
        )
    )

    return _theme(bars + labels, "Eficiencia Ambiental — kg CO₂ por Kilómetro")
