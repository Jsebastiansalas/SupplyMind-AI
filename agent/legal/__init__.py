"""
agent/legal/__init__.py
Módulos jurídicos, tratados internacionales (CISG, T-MEC) y peritajes de arbitraje.
"""

from agent.legal.cross_border_treaties import (
    TreatyArticle,
    CrossBorderEvaluationResult,
    CrossBorderTreatiesEngine,
)

__all__ = [
    "TreatyArticle",
    "CrossBorderEvaluationResult",
    "CrossBorderTreatiesEngine",
]
