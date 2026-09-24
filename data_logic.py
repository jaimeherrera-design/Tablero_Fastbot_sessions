from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


REQUIRED_COLUMNS = {
    "session_start_fecha",
    "session_start_hora",
    "duracion_total",
    "user_started_session",
    "not_available_agent_session",
    "category",
    "agent_id",
    "bsuid",
    "botname",
    "operator_id",
    "cuenta",
}
METRIC_COLUMNS = [
    "cuenta",
    "user_started_session",
    "not_available_agent_session",
    "duracion_total",
]
DIMENSION_COLUMNS = ["category", "agent_id", "bsuid", "botname", "operator_id"]


def discover_csv_files(data_dir: Path) -> list[Path]:
    return sorted(path for path in data_dir.glob("*.csv") if path.is_file())


def load_and_consolidate(files: Iterable[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    for source_order, path in enumerate(sorted(files, key=lambda item: (item.stat().st_mtime_ns, item.name))):
        frame = pd.read_csv(path, low_memory=False)
        missing = REQUIRED_COLUMNS.difference(frame.columns)
        if missing:
            missing_names = ", ".join(sorted(missing))
            raise ValueError(f"{path.name} no contiene las columnas requeridas: {missing_names}")

        frame = frame[list(REQUIRED_COLUMNS)].copy()
        frame["fecha"] = pd.to_datetime(frame.pop("session_start_fecha"), errors="coerce")
        frame["hora"] = pd.to_numeric(frame.pop("session_start_hora"), errors="coerce")
        for column in METRIC_COLUMNS:
            frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0).clip(lower=0)

        for column in DIMENSION_COLUMNS:
            frame[column] = frame[column].astype("string").fillna("Sin dato").replace("", "Sin dato")
        frame = frame.dropna(subset=["fecha", "hora"])
        frame["hora"] = frame["hora"].astype(int).clip(0, 23)
        frame["_source_order"] = source_order
        frame["_source_file"] = path.name
        frames.append(frame)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    data_columns = ["fecha", "hora", *DIMENSION_COLUMNS, *METRIC_COLUMNS]
    combined = combined.sort_values("_source_order").drop_duplicates(subset=data_columns, keep="last")

    combined["mes"] = combined["fecha"].dt.to_period("M").dt.to_timestamp()
    combined["dia"] = combined["fecha"].dt.day
    combined["dia_semana"] = combined["fecha"].dt.day_name(locale="C")
    combined["fecha_hora"] = combined["fecha"] + pd.to_timedelta(combined["hora"], unit="h")
    return combined.sort_values(["fecha", "hora", "botname", "category"]).reset_index(drop=True)


def percent_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return (current - previous) / previous * 100


def current_month_comparison(
    frame: pd.DataFrame, metric: str = "cuenta"
) -> dict[str, float | int | pd.Timestamp | None]:
    if metric not in METRIC_COLUMNS:
        raise ValueError(f"Métrica no soportada: {metric}")
    if frame.empty:
        return {
            "current": 0.0,
            "previous": 0.0,
            "variation": None,
            "cutoff_day": 0,
            "current_month": None,
            "previous_month": None,
        }

    max_date = frame["fecha"].max()
    current_month = max_date.to_period("M")
    previous_month = current_month - 1
    cutoff_day = int(max_date.day)

    current_mask = frame["fecha"].dt.to_period("M").eq(current_month) & frame["dia"].le(cutoff_day)
    previous_mask = frame["fecha"].dt.to_period("M").eq(previous_month) & frame["dia"].le(cutoff_day)
    current = float(frame.loc[current_mask, metric].sum())
    previous = float(frame.loc[previous_mask, metric].sum())

    return {
        "current": current,
        "previous": previous,
        "variation": percent_change(current, previous),
        "cutoff_day": cutoff_day,
        "current_month": current_month.to_timestamp(),
        "previous_month": previous_month.to_timestamp(),
    }


def aggregate_with_variation(
    frame: pd.DataFrame, period: str, metric: str = "cuenta"
) -> pd.DataFrame:
    if metric not in METRIC_COLUMNS:
        raise ValueError(f"Métrica no soportada: {metric}")
    if frame.empty:
        return pd.DataFrame(columns=[period, metric, "variacion"])
    if period not in {"mes", "fecha", "hora"}:
        raise ValueError(f"Periodo no soportado: {period}")

    grouped = frame.groupby(period, as_index=False)[metric].sum().sort_values(period)
    grouped["variacion"] = grouped[metric].pct_change(fill_method=None) * 100
    return grouped
