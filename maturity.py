"""Nurse-Saul maturity calculation + a synthetic strength-maturity calibration curve
(not derived from any real tested mix design; illustrative only)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

DEFAULT_DATUM_TEMP_F = 14.0  # ASTM C1074 commonly-used default datum temperature


def nurse_saul_maturity(readings: pd.DataFrame, datum_temp_f: float = DEFAULT_DATUM_TEMP_F) -> pd.DataFrame:
    """M(t) = sum((T_a - T0) * dt) over `readings` (columns: timestamp, temp_f).

    Returns a copy sorted by timestamp with added "elapsed_hours" and
    "maturity_degree_hours" columns.

    Hand check: two readings 1h apart at a constant 70F, datum 14F ->
    M = (70 - 14) * 1 = 56 degree-hours.
    >>> df = pd.DataFrame({
    ...     "timestamp": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 01:00"]),
    ...     "temp_f": [70.0, 70.0],
    ... })
    >>> float(nurse_saul_maturity(df)["maturity_degree_hours"].iloc[-1])
    56.0
    """
    if readings.empty:
        return readings.assign(elapsed_hours=pd.Series(dtype=float), maturity_degree_hours=pd.Series(dtype=float))

    df = readings.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    elapsed_hours = (df["timestamp"] - df["timestamp"].iloc[0]).dt.total_seconds() / 3600.0
    df["elapsed_hours"] = elapsed_hours

    maturity = np.zeros(len(df))
    for i in range(1, len(df)):
        dt_hours = elapsed_hours.iloc[i] - elapsed_hours.iloc[i - 1]
        t_avg = (df["temp_f"].iloc[i] + df["temp_f"].iloc[i - 1]) / 2.0
        increment = max(t_avg - datum_temp_f, 0.0) * dt_hours
        maturity[i] = maturity[i - 1] + increment

    df["maturity_degree_hours"] = maturity
    return df


def maturity_at_target(target_psi: float, m_base: float = 5100.0, ref_psi: float = 3000.0, exponent: float = 1.5) -> float:
    """Synthetic maturity index (degree-hours) at which the illustrative curve reaches `target_psi`."""
    return m_base * (target_psi / ref_psi) ** exponent


def estimate_strength_psi(maturity_degree_hours, target_psi: float, m1_fraction: float = 0.1):
    """Illustrative logarithmic strength-maturity curve, not from real mix data. Reaches
    `target_psi` around the maturity from `maturity_at_target`, then keeps rising slowly,
    same as real concrete continuing to gain strength past an early-age threshold."""
    m = np.asarray(maturity_degree_hours, dtype=float)
    m = np.clip(m, 0.0, None)

    m_target = maturity_at_target(target_psi)
    m1 = m1_fraction * m_target

    numerator = np.log1p(m / m1)
    denominator = math.log1p(m_target / m1)
    strength = target_psi * numerator / denominator

    if np.isscalar(maturity_degree_hours):
        return float(strength)
    return strength
