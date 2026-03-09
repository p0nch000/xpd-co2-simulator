"""Excel export utilities."""

from __future__ import annotations

from io import BytesIO

import pandas as pd


def build_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    """Write multiple DataFrames to an in-memory Excel workbook."""
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, df in sheets.items():
            if df is not None and not df.empty:
                df.to_excel(writer, index=False, sheet_name=str(name)[:31])
    buf.seek(0)
    return buf.getvalue()
