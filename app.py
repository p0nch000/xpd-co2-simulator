"""
XPD CO₂ Logistics Simulator — Streamlit entry point.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from src.charts import (
    bar_co2_by_route,
    bar_co2_by_vehicle,
    bar_efficiency,
    donut_participation,
    scatter_cost_vs_co2,
)
from src.constants import DEFAULT_FLEET, DEFAULT_FUELS, DEFAULT_ROUTES, XPD_BLUE, XPD_NAVY, XPD_ORANGE
from src.engine import motor_detallado_v2, resumen_por_ruta, resumen_por_unidad, top3
from src.export import build_excel_bytes
from src.persistence import build_payload, read_payload, write_payload
from src.utils import df_hash, records_to_df
from src.validators import normalizar_rutas, validar_combustibles, validar_flota

# ─────────────────────────────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="XPD CO₂ Logistics Simulator",
    page_icon="assets/xpd-logo.png",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────────────
# XPD Brand CSS
# ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Global reset ────────────────────────────────── */
    html, body, [data-testid="stAppViewContainer"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased;
    }}


    /* ── Header bar ─────────────────────────────────────── */
    header[data-testid="stHeader"] {{
        background: linear-gradient(90deg, {XPD_NAVY} 0%, {XPD_BLUE} 100%);
    }}

    /* ── Typography ─────────────────────────────────────── */
    .stMarkdown h2 {{
        color: {XPD_NAVY} !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
    }}
    .stMarkdown h3 {{
        color: {XPD_NAVY} !important;
        font-weight: 500 !important;
    }}

    /* ── Subheader accent ───────────────────────────────── */
    [data-testid="stSubheader"] {{
        border-left: 3px solid {XPD_BLUE};
        padding-left: 14px;
    }}

    /* ── Primary button ─────────────────────────────────── */
    .stButton > button[kind="primary"],
    button[data-testid="stBaseButton-primary"] {{
        background-color: {XPD_BLUE} !important;
        border: none !important;
        color: white !important;
        font-weight: 600;
        border-radius: 8px !important;
        transition: all 0.2s ease;
    }}
    .stButton > button[kind="primary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover {{
        background-color: {XPD_NAVY} !important;
    }}

    /* ── Secondary buttons ──────────────────────────────── */
    .stButton > button:not([kind="primary"]),
    button[data-testid="stBaseButton-secondary"] {{
        border: 1.5px solid {XPD_BLUE} !important;
        color: {XPD_BLUE} !important;
        font-weight: 500;
        border-radius: 8px !important;
        transition: all 0.2s ease;
    }}
    .stButton > button:not([kind="primary"]):hover,
    button[data-testid="stBaseButton-secondary"]:hover {{
        background-color: {XPD_BLUE} !important;
        color: white !important;
    }}

    /* ── Download buttons ───────────────────────────────── */
    .stDownloadButton > button {{
        border: 1.5px solid {XPD_BLUE} !important;
        color: {XPD_BLUE} !important;
        font-weight: 500;
        border-radius: 8px !important;
    }}
    .stDownloadButton > button:hover {{
        background-color: {XPD_BLUE} !important;
        color: white !important;
    }}

    /* ── Tabs ───────────────────────────────────────────── */
    button[data-baseweb="tab"] {{
        color: {XPD_NAVY} !important;
        font-weight: 500;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {XPD_BLUE} !important;
        border-bottom-color: {XPD_BLUE} !important;
    }}

    /* ── Metrics ────────────────────────────────────────── */
    [data-testid="stMetricLabel"] {{
        color: {XPD_NAVY};
        font-weight: 600;
    }}
    [data-testid="stMetricValue"] {{
        color: {XPD_BLUE};
    }}

    /* ── Slider thumb ──────────────────────────────────── */
    .stSlider [data-testid="stThumbValue"] {{
        color: {XPD_BLUE};
    }}

    /* ── Dividers ──────────────────────────────────────── */
    hr {{
        border-top: 2px solid {XPD_BLUE}20 !important;
    }}

    /* ── Toggle ────────────────────────────────────────── */
    [data-testid="stToggle"] label span {{
        color: {XPD_NAVY};
    }}

    /* ── Data editor / tables ─────────────────────────── */
    .stDataFrame {{
        border: 1px solid {XPD_BLUE}15;
        border-radius: 8px;
    }}

    /* ── XPD styled HTML tables ───────────────────────── */
    .xpd-table {{
        width: 100%;
        border-collapse: collapse;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
    }}
    .xpd-table thead th {{
        background-color: {XPD_BLUE};
        color: #ffffff;
        font-weight: 600;
        padding: 10px 14px;
        text-align: left;
        white-space: nowrap;
        border-bottom: 2px solid {XPD_NAVY};
    }}
    .xpd-table tbody td {{
        padding: 8px 14px;
        border-bottom: 1px solid #f0f0f0;
        color: {XPD_NAVY};
    }}
    .xpd-table tbody tr:hover {{
        background-color: {XPD_BLUE}08;
    }}
    .xpd-table tbody tr:nth-child(even) {{
        background-color: #f9fafb;
    }}

</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# XPD Logo + Title
# ─────────────────────────────────────────────────────────────────────
_logo_path = Path(__file__).parent / "assets" / "xpd-logo.png"
if _logo_path.exists():
    _logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode()
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:16px; margin-bottom:4px;">
        <img src="data:image/png;base64,{_logo_b64}" height="52" />
        <div>
            <h1 style="margin:0; color:{XPD_NAVY}; font-size:1.8rem; font-weight:700; letter-spacing:-0.02em; font-family:'Inter',sans-serif;">
                Simulador CO₂ Logístico
            </h1>
            <p style="margin:2px 0 0 0; color:#888; font-size:0.82rem; letter-spacing:0.02em; font-weight:400;">
                Precisión operativa · Reportes ESG · Cadena de frío · Combustibles dinámicos
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.title("Simulador CO₂ Logístico — XPD Global")
    st.caption(
        "Precisión operativa · Reportes ESG · "
        "Cadena de frío · Combustibles dinámicos"
    )
st.divider()

# ─────────────────────────────────────────────────────────────────────
# Session State Initialisation
# ─────────────────────────────────────────────────────────────────────
_SCENARIOS = ("A", "B")
_DATA_KEYS = {
    "comb": "combustibles",
    "flotaA": "flota_A",
    "flotaB": "flota_B",
    "rutasA": "rutas_A",
    "rutasB": "rutas_B",
}


def _init_session() -> None:
    """Bootstrap session state from disk or defaults (runs once)."""
    if "editor_ver" not in st.session_state:
        st.session_state.editor_ver = 0

    if "saved_at" in st.session_state:
        return

    disk = read_payload()
    if disk:
        st.session_state.saved_at = disk.get("saved_at", "")
        st.session_state.saved_comb = validar_combustibles(
            records_to_df(disk.get("combustibles", []))
        )
        st.session_state.saved_flotaA = validar_flota(
            records_to_df(disk.get("flota_A", [])), "A"
        )
        st.session_state.saved_flotaB = validar_flota(
            records_to_df(disk.get("flota_B", [])), "B"
        )
        st.session_state.saved_rutasA = records_to_df(disk.get("rutas_A", []))
        st.session_state.saved_rutasB = records_to_df(disk.get("rutas_B", []))
    else:
        st.session_state.saved_at = ""
        st.session_state.saved_comb = DEFAULT_FUELS.copy()
        st.session_state.saved_flotaA = DEFAULT_FLEET.copy()
        st.session_state.saved_flotaB = DEFAULT_FLEET.copy()
        st.session_state.saved_rutasA = DEFAULT_ROUTES.copy()
        st.session_state.saved_rutasB = DEFAULT_ROUTES.copy()

    # Working copies
    for suffix in ("comb", "flotaA", "flotaB", "rutasA", "rutasB"):
        saved = st.session_state[f"saved_{suffix}"]
        for prefix in ("work", "buf"):
            key = f"{prefix}_{suffix}"
            if key not in st.session_state:
                st.session_state[key] = saved.copy()


_init_session()


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────
def _xpd_table(df: pd.DataFrame, fmt: dict | None = None) -> None:
    """Render a DataFrame as a styled HTML table with XPD blue headers."""
    if df.empty:
        st.info("Sin datos.")
        return
    fmt = fmt or {}
    header = "".join(f"<th>{c}</th>" for c in df.columns)
    rows = []
    for _, row in df.iterrows():
        cells = []
        for c in df.columns:
            v = row[c]
            if c in fmt:
                cells.append(f"<td>{fmt[c].format(v)}</td>")
            elif isinstance(v, float):
                cells.append(f"<td>{v:,.2f}</td>")
            else:
                cells.append(f"<td>{v}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    html = f'<table class="xpd-table"><thead><tr>{header}</tr></thead><tbody>{chr(10).join(rows)}</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)


def _state_hash(prefix: str) -> str:
    return "".join(
        df_hash(st.session_state[f"{prefix}_{s}"])
        for s in ("comb", "flotaA", "flotaB", "rutasA", "rutasB")
    )


def _copy_layer(src: str, dst: str) -> None:
    """Copy all DataFrames from one state layer to another."""
    for suffix in ("comb", "flotaA", "flotaB", "rutasA", "rutasB"):
        st.session_state[f"{dst}_{suffix}"] = st.session_state[f"{src}_{suffix}"].copy()


def _bump_editor() -> None:
    st.session_state.editor_ver += 1


def _current_payload() -> dict:
    return build_payload(
        st.session_state.work_flotaA,
        st.session_state.work_flotaB,
        st.session_state.work_rutasA,
        st.session_state.work_rutasB,
        st.session_state.work_comb,
    )


# ─────────────────────────────────────────────────────────────────────
# 1) Global Parameters
# ─────────────────────────────────────────────────────────────────────
st.subheader("1 · Parámetros Logísticos Globales")
p1, p2, p3 = st.columns(3)
penal_urbana = p1.slider(
    "Castigo Máximo Urbano (%)", 0, 60, 30,
    help="Reduce el rendimiento en trayectos de ciudad.",
)
pct_llenado = p2.slider(
    "Ocupación Global de Cajas (%)", 0, 100, 100,
    help="Si es menor a 100%, otorga un bono automático de rendimiento al motor.",
)
km_min = p3.number_input(
    "KM mínimo en Rutas (Local)", min_value=0.0, value=35.0, step=5.0,
)
st.divider()

# ─────────────────────────────────────────────────────────────────────
# 2) Save / Load
# ─────────────────────────────────────────────────────────────────────
st.subheader("2 · Guardar Panel (Local)")

saved_hash = _state_hash("saved")
work_hash = _state_hash("work")

col_status, col_actions = st.columns([2, 3])

with col_status:
    if work_hash != saved_hash:
        st.warning("Tienes cambios sin guardar.")
    else:
        st.success("Datos actualizados y sincronizados.")
    ts = st.session_state.saved_at
    st.caption(f"Último guardado: {ts}" if ts else "Aún no se ha guardado en disco.")

    uploaded = st.file_uploader(
        "Abrir configuración externa (JSON)", type=["json"],
    )
    if uploaded is not None:
        ext = json.loads(uploaded.getvalue().decode("utf-8"))
        st.session_state.work_flotaA = validar_flota(
            records_to_df(ext.get("flota_A", [])), "A"
        )
        st.session_state.work_flotaB = validar_flota(
            records_to_df(ext.get("flota_B", [])), "B"
        )
        st.session_state.work_rutasA = normalizar_rutas(
            records_to_df(ext.get("rutas_A", [])), km_min
        )
        st.session_state.work_rutasB = normalizar_rutas(
            records_to_df(ext.get("rutas_B", [])), km_min
        )
        st.session_state.work_comb = validar_combustibles(
            records_to_df(ext.get("combustibles", []))
        )
        st.info(
            "Configuración cargada en modo trabajo. "
            "Presiona 'Guardar' para oficializarla."
        )

with col_actions:
    b1, b2, b3, b4 = st.columns(4)

    if b1.button("Guardar", use_container_width=True):
        _copy_layer("work", "saved")
        st.session_state.saved_at = datetime.now().isoformat(timespec="seconds")
        write_payload(_current_payload())
        st.rerun()

    if b2.button("Deshacer", use_container_width=True):
        _copy_layer("saved", "work")
        _copy_layer("work", "buf")
        _bump_editor()
        st.rerun()

    if b3.button("Recargar", use_container_width=True):
        disk = read_payload()
        if disk:
            st.session_state.saved_at = disk.get("saved_at", "")
            st.session_state.saved_comb = validar_combustibles(
                records_to_df(disk.get("combustibles", []))
            )
            st.session_state.saved_flotaA = validar_flota(
                records_to_df(disk.get("flota_A", [])), "A"
            )
            st.session_state.saved_flotaB = validar_flota(
                records_to_df(disk.get("flota_B", [])), "B"
            )
            st.session_state.saved_rutasA = records_to_df(disk.get("rutas_A", []))
            st.session_state.saved_rutasB = records_to_df(disk.get("rutas_B", []))
            _copy_layer("saved", "work")
            _copy_layer("work", "buf")
            _bump_editor()
            st.rerun()

    cfg_bytes = json.dumps(
        _current_payload(), ensure_ascii=False, indent=2
    ).encode("utf-8")
    b4.download_button(
        "Exportar JSON", data=cfg_bytes,
        file_name="config_emisiones_v2.json",
        mime="application/json", use_container_width=True,
    )

st.divider()

# ─────────────────────────────────────────────────────────────────────
# 3) Fuel Editor
# ─────────────────────────────────────────────────────────────────────
st.subheader("3 · Combustibles (Factor CO₂ y Precios)")
comb_edited = st.data_editor(
    st.session_state.buf_comb,
    key=f"comb_{st.session_state.editor_ver}",
    num_rows="dynamic", hide_index=True, use_container_width=True,
)
if df_hash(comb_edited) != df_hash(st.session_state.work_comb):
    if st.button("Aplicar Cambios de Combustibles"):
        st.session_state.work_comb = validar_combustibles(comb_edited.copy())
        st.session_state.buf_comb = st.session_state.work_comb.copy()
        _bump_editor()
        st.rerun()

st.divider()

# ───────────────────────────────────────────────────────────────────
# 4) Fleet Editor (A vs B)
# ───────────────────────────────────────────────────────────────────
st.subheader("4 · Distribución de Flota")
st.caption("Configura la composición vehicular para cada escenario de simulación")
fuel_list = st.session_state.work_comb["Combustible"].tolist()
fuel_col_cfg = st.column_config.SelectboxColumn(
    "Combustible", options=fuel_list, required=True,
)

col_a, col_b = st.columns(2, gap="large")
for label, col, accent in [("A", col_a, XPD_BLUE), ("B", col_b, XPD_ORANGE)]:
    with col:
        st.markdown(
            f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">'
            f'<div style="width:10px; height:10px; border-radius:50%; background:{accent};"></div>'
            f'<span style="color:{XPD_NAVY}; font-weight:600; font-size:1rem;">Escenario {label}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        buf_key = f"buf_flota{label}"
        work_key = f"work_flota{label}"
        edited = st.data_editor(
            st.session_state[buf_key],
            key=f"flota{label}_{st.session_state.editor_ver}",
            num_rows="dynamic", hide_index=True,
            column_config={"Combustible": fuel_col_cfg},
            use_container_width=True,
        )
        if df_hash(edited) != df_hash(st.session_state[work_key]):
            if st.button(f"Aplicar Flota {label}", use_container_width=True):
                st.session_state[work_key] = validar_flota(edited.copy(), label)
                st.session_state[buf_key] = st.session_state[work_key].copy()
                _bump_editor()
                st.rerun()

# Validate both fleets for blocking
st.session_state.work_flotaA = validar_flota(st.session_state.work_flotaA, "A")
st.session_state.work_flotaB = validar_flota(st.session_state.work_flotaB, "B")
st.session_state.bloquear_calculo = bool(
    st.session_state.get("bloquear_A") or st.session_state.get("bloquear_B")
)
st.divider()

# ─────────────────────────────────────────────────────────────────────
# 5) Route Editor (A vs B)
# ─────────────────────────────────────────────────────────────────────
st.subheader("5 · Configuración de Rutas")
st.caption("Red de rutas y parámetros logísticos por escenario")
routes_col_cfg = {
    "Horas_Demora": st.column_config.NumberColumn(
        "Horas_Demora (h, editable)",
        help=(
            "Puedes capturar horas decimales (ej. 0.25, 0.5, 1, 2). "
            "Si lo dejas vacío, se autocalcula por KM."
        ),
        min_value=0.0, step=0.25, format="%.2f",
    ),
    "Demora_Sugerida": st.column_config.TextColumn(
        "Demora sugerida (según KM)",
        help="<=50=15 min, <=200=30 min, <=500=1 hora, >500=2 horas",
        disabled=True,
    ),
}

ra, rb = st.columns(2, gap="large")
for label, col, accent in [("A", ra, XPD_BLUE), ("B", rb, XPD_ORANGE)]:
    with col:
        st.markdown(
            f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">'
            f'<div style="width:10px; height:10px; border-radius:50%; background:{accent};"></div>'
            f'<span style="color:{XPD_NAVY}; font-weight:600; font-size:1rem;">Rutas {label}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        buf_key = f"buf_rutas{label}"
        work_key = f"work_rutas{label}"
        view = normalizar_rutas(st.session_state[buf_key], km_min)
        edited = st.data_editor(
            view,
            key=f"rutas{label}_{st.session_state.editor_ver}",
            num_rows="dynamic", hide_index=True,
            column_config=routes_col_cfg,
            use_container_width=True,
        )
        if df_hash(edited) != df_hash(st.session_state[work_key]):
            if st.button(f"Aplicar Rutas {label}", use_container_width=True):
                st.session_state[work_key] = edited.copy()
                st.session_state[buf_key] = st.session_state[work_key].copy()
                _bump_editor()
                st.rerun()

rutasA_norm = normalizar_rutas(st.session_state.work_rutasA, km_min)
rutasB_norm = normalizar_rutas(st.session_state.work_rutasB, km_min)
st.divider()

# ─────────────────────────────────────────────────────────────────────
# Data-prep helpers (dashboard)
# ─────────────────────────────────────────────────────────────────────
def _build_comparison(detA: pd.DataFrame, detB: pd.DataFrame) -> pd.DataFrame:
    """Melt A/B CO₂ by vehicle into long format."""
    def _agg(det: pd.DataFrame, suffix: str) -> pd.DataFrame:
        if det.empty:
            return pd.DataFrame(columns=["Unidad", f"CO2_{suffix}"])
        return det.groupby("Unidad", as_index=False)["CO2_kg"].sum().rename(
            columns={"CO2_kg": f"CO2_{suffix}"}
        )

    comp = _agg(detA, "A").merge(_agg(detB, "B"), on="Unidad", how="outer").fillna(0)
    long = comp.melt(id_vars="Unidad", var_name="Escenario", value_name="CO2_kg")
    long["tCO2"] = long["CO2_kg"] / 1000.0
    return long


def _build_route_comparison(
    rutA: pd.DataFrame, rutB: pd.DataFrame,
) -> pd.DataFrame:
    """Combine route summaries into long format."""
    frames: list[pd.DataFrame] = []
    for df, esc in [(rutA, "A"), (rutB, "B")]:
        if not df.empty:
            tmp = df.copy()
            tmp["Escenario"] = esc
            frames.append(tmp)
    if not frames:
        return pd.DataFrame(columns=["Tramo", "CO2_kg", "Escenario", "tCO2"])
    out = pd.concat(frames, ignore_index=True)
    out["tCO2"] = np.where(pd.notna(out["CO2_kg"]), out["CO2_kg"] / 1000.0, 0.0)
    return out


def _build_participation(
    resA: pd.DataFrame, resB: pd.DataFrame,
) -> pd.DataFrame:
    """Combine unit participation data for both scenarios."""
    cols = ["Unidad", "CO2_kg", "%_CO2", "Costo_MXN"]
    frames: list[pd.DataFrame] = []
    for df, esc in [(resA, "A"), (resB, "B")]:
        tmp = df[cols].copy() if not df.empty else pd.DataFrame(columns=cols)
        tmp["Escenario"] = esc
        frames.append(tmp)
    return pd.concat(frames, ignore_index=True)


def _build_efficiency(
    resA: pd.DataFrame, resB: pd.DataFrame,
) -> pd.DataFrame:
    """Combine efficiency metrics for both scenarios."""
    cols = ["Unidad", "CO2_kg_por_km", "Costo_por_km"]
    frames: list[pd.DataFrame] = []
    for df, esc in [(resA, "A"), (resB, "B")]:
        tmp = df[cols].copy() if not df.empty else pd.DataFrame(columns=cols)
        tmp["Escenario"] = esc
        frames.append(tmp)
    return pd.concat(frames, ignore_index=True)


# ─────────────────────────────────────────────────────────────────────
# 6) Run Calculation
# ─────────────────────────────────────────────────────────────────────
st.subheader("6 · Análisis Ejecutivo y Emisiones")
ver_solo_refri = st.toggle("Analizar únicamente Cadena de Frío", value=False)

if st.session_state.bloquear_calculo:
    st.error(
        "Cálculo bloqueado: corrige primero los errores en las tablas de Flota."
    )

run = st.button(
    "Ejecutar Cálculo de Emisiones",
    type="primary", use_container_width=True,
    disabled=st.session_state.bloquear_calculo,
)

if run:
    comb_ok = validar_combustibles(st.session_state.work_comb)

    detA = motor_detallado_v2(
        st.session_state.work_flotaA, rutasA_norm, comb_ok,
        penal_urbana, pct_llenado, ver_solo_refri,
    )
    detB = motor_detallado_v2(
        st.session_state.work_flotaB, rutasB_norm, comb_ok,
        penal_urbana, pct_llenado, ver_solo_refri,
    )

    co2A = float(detA["CO2_kg"].sum()) if not detA.empty else 0.0
    co2B = float(detB["CO2_kg"].sum()) if not detB.empty else 0.0

    if co2A == 0 and co2B == 0:
        st.error(
            "No hay operaciones válidas para calcular "
            "(revisa rutas y porcentajes de flota)."
        )
        st.stop()

    # Persist results so the dashboard survives widget interactions
    st.session_state.calc_results = {
        "detA": detA, "detB": detB,
        "resA": resumen_por_unidad(detA), "resB": resumen_por_unidad(detB),
        "rutA": resumen_por_ruta(detA), "rutB": resumen_por_ruta(detB),
    }

# ── Render results (persisted across reruns) ─────────────────────
if "calc_results" in st.session_state:
    _r = st.session_state.calc_results
    detA, detB = _r["detA"], _r["detB"]
    resA, resB = _r["resA"], _r["resB"]
    rutA, rutB = _r["rutA"], _r["rutB"]

    co2A = float(detA["CO2_kg"].sum()) if not detA.empty else 0.0
    co2B = float(detB["CO2_kg"].sum()) if not detB.empty else 0.0
    costA = float(detA["Costo_MXN"].sum()) if not detA.empty else 0.0
    costB = float(detB["Costo_MXN"].sum()) if not detB.empty else 0.0
    ahorro_co2 = co2A - co2B
    ahorro_cost = costA - costB
    pct = "—" if co2A == 0 else f"{(ahorro_co2 / co2A) * 100:.1f}%"

    # ── KPIs ─────────────────────────────────────────────────
    st.subheader("Resultados Consolidados")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("CO₂ A (kg)", f"{co2A:,.0f}")
    k2.metric("CO₂ B (kg)", f"{co2B:,.0f}", delta=f"{-ahorro_co2:,.0f} kg ({pct})")
    k3.metric("Costo Operativo A", f"${costA:,.0f}")
    k4.metric("Costo Operativo B", f"${costB:,.0f}", delta=f"${-ahorro_cost:,.0f}")
    st.divider()

    # ── Summaries ────────────────────────────────────────────
    st.subheader("Desglose y Participación (%)")
    c1, c2 = st.columns(2)
    _tbl_fmt = {"%_CO2": "{:.1f}%", "CO2_kg_por_km": "{:.2f}", "CO2_kg": "{:,.0f}", "Costo_MXN": "${:,.0f}", "Costo_por_km": "${:,.2f}"}
    with c1:
        st.markdown("### Unidades — Escenario A")
        _xpd_table(resA, _tbl_fmt)
    with c2:
        st.markdown("### Unidades — Escenario B")
        _xpd_table(resB, _tbl_fmt)

    st.subheader("Top 3 Drivers de Contaminación")
    t1, t2, t3, t4 = st.columns(4)
    for col, title, data, cols in [
        (t1, "Top Unidades A", resA, ["Unidad", "CO2_kg", "%_CO2"]),
        (t2, "Top Unidades B", resB, ["Unidad", "CO2_kg", "%_CO2"]),
        (t3, "Top Rutas A", rutA, ["Tramo", "CO2_kg", "%_CO2"]),
        (t4, "Top Rutas B", rutB, ["Tramo", "CO2_kg", "%_CO2"]),
    ]:
        with col:
            st.markdown(f"**{title}**")
            if not data.empty:
                _xpd_table(top3(data)[cols], {"%_CO2": "{:.1f}%", "CO2_kg": "{:,.0f}"})
    st.divider()

    # ── Comparative Bar Chart ────────────────────────────────────
    st.subheader("Comparativa CO₂ por Tipo de Vehículo")
    comp = _build_comparison(detA, detB)
    if not comp.empty:
        st.altair_chart(bar_co2_by_vehicle(comp), use_container_width=True)
    st.divider()

    # ── Audit Export ─────────────────────────────────────────
    audit_sheets = {
        "Resumen_Unidades_A": resA,
        "Resumen_Unidades_B": resB,
        "Resumen_Rutas_A": rutA,
        "Resumen_Rutas_B": rutB,
        "Detalle_Operacion_A": detA,
        "Detalle_Operacion_B": detB,
    }
    st.download_button(
        "Descargar Excel Completo (Auditoría)",
        data=build_excel_bytes(audit_sheets),
        file_name="Reporte_ESG_XPD.xlsx",
        use_container_width=True,
    )

    with st.expander("Ver desglose matemático exacto (Escenario A)"):
        _xpd_table(detA, {"CO2_kg": "{:,.2f}", "Costo_MXN": "${:,.2f}"})
    with st.expander("Ver desglose matemático exacto (Escenario B)"):
        _xpd_table(detB, {"CO2_kg": "{:,.2f}", "Costo_MXN": "${:,.2f}"})

    # ─────────────────────────────────────────────────────────────
    # 7) Visual Dashboard
    # ─────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("7 · Dashboard Visual")

    comp_long = _build_comparison(detA, detB)
    ruta_long = _build_route_comparison(rutA, rutB)
    part_long = _build_participation(resA, resB)
    eff_long = _build_efficiency(resA, resB)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Comparativa A vs B",
        "CO₂ por Ruta",
        "Participación por Unidad",
        "Costo vs CO₂",
        "Eficiencia",
    ])

    with tab1:
        if not comp_long.empty:
            st.altair_chart(bar_co2_by_vehicle(comp_long), use_container_width=True)
        st.download_button(
            "Descargar datos — Comparativa",
            data=build_excel_bytes({"Datos_Comp_CO2": comp_long}),
            file_name="datos_comparativa_co2.xlsx", use_container_width=True,
        )

    with tab2:
        if not ruta_long.empty and "Tramo" in ruta_long.columns:
            st.altair_chart(bar_co2_by_route(ruta_long), use_container_width=True)
        st.download_button(
            "Descargar datos — CO₂ por Ruta",
            data=build_excel_bytes({"Datos_CO2_Ruta": ruta_long}),
            file_name="datos_co2_por_ruta.xlsx", use_container_width=True,
        )

    with tab3:
        if not part_long.empty:
            sel = st.selectbox("Escenario", ["A", "B"], index=0, key="sel_part")
            dfp = part_long[part_long["Escenario"] == sel]
            if not dfp.empty:
                st.altair_chart(donut_participation(dfp), use_container_width=True)
        st.download_button(
            "Descargar datos — Participación",
            data=build_excel_bytes({"Datos_Participacion": part_long}),
            file_name="datos_participacion_co2.xlsx", use_container_width=True,
        )

    with tab4:
        if not part_long.empty:
            st.altair_chart(scatter_cost_vs_co2(part_long), use_container_width=True)
        st.download_button(
            "Descargar datos — Costo vs CO₂",
            data=build_excel_bytes({"Datos_Costo_vs_CO2": part_long}),
            file_name="datos_costo_vs_co2.xlsx", use_container_width=True,
        )

    with tab5:
        if not eff_long.empty:
            st.altair_chart(bar_efficiency(eff_long), use_container_width=True)
        st.download_button(
            "Descargar datos — Eficiencia",
            data=build_excel_bytes({"Datos_Eficiencia": eff_long}),
            file_name="datos_eficiencia.xlsx", use_container_width=True,
        )

    st.divider()
    pack = {
        "Datos_Comp_CO2": comp_long,
        "Datos_CO2_Ruta": ruta_long,
        "Datos_Participacion": part_long,
        "Datos_Eficiencia": eff_long,
    }
    st.download_button(
        "Descargar Paquete Visual (todas las tablas)",
        data=build_excel_bytes(pack),
        file_name="Paquete_Visual_Graficas.xlsx", use_container_width=True,
    )
