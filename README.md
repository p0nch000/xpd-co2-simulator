# XPD CO₂ Logistics Simulator

Streamlit-based CO₂ logistics simulator for **XPD Global**. Models fleet
emissions across two operational scenarios (A vs B) with full audit exports.

## Features

- **Scenario comparison** — side-by-side fleet & route configuration
- **Refrigerated transport** — per-route or global cold-chain percentages
- **Urban proportional routing** — configurable city-driving penalty
- **Idle consumption** — automatic delay estimation by route distance
- **Dynamic fuels** — supports litres (L) and kilowatt-hours (kWh)
- **Excel audit exports** — full breakdown + visual dashboard pack
- **JSON persistence** — save/load/undo/reload working state

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project Structure

```
app.py                  ← Streamlit entry point
src/
  constants.py          ← Brand palette, defaults, thresholds
  utils.py              ← Pure utility functions
  validators.py         ← Input validation (fuels, fleet, routes)
  engine.py             ← CO₂ calculation engine & summaries
  persistence.py        ← JSON save/load
  charts.py             ← Altair chart builders (XPD brand colors)
  export.py             ← Excel export
.streamlit/config.toml  ← XPD-themed Streamlit config
```
