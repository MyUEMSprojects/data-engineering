"""Detecção de anomalias ROBUSTA (mediana/MAD) contra o histórico de lotes publicados.

Por que mediana/MAD e não média/desvio-padrão? Um único valor atípico no histórico
infla o desvio-padrão e "esconde" a próxima anomalia; mediana/MAD resistem a outliers.
"""

from __future__ import annotations

from statistics import median


def robust_z(value: float, history: list[float]) -> float:
    """z-score robusto (0.6745·(x−mediana)/MAD). Piso no MAD evita divisão por ~0."""
    med = median(history)
    mad = median(abs(h - med) for h in history)
    scale = max(mad, 0.01 * abs(med), 1e-9)
    return 0.6745 * (value - med) / scale


def is_anomalous(
    value: float, history: list[float], z_max: float, min_history: int
) -> tuple[bool | None, float | None]:
    """(anômalo?, z). `None` => histórico insuficiente (check é PULADO, não aprovado às cegas)."""
    if len(history) < min_history:
        return None, None
    z = robust_z(value, history)
    return abs(z) > z_max, z
