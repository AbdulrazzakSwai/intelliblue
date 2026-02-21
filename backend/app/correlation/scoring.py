"""
Severity and confidence scoring utilities.
"""
from ..models.incident import IncidentSeverity


def compute_severity(confidence: int, ids_corroborated: bool = False) -> str:
    if confidence >= 85 or ids_corroborated:
        return IncidentSeverity.HIGH.value
    if confidence >= 65:
        return IncidentSeverity.MEDIUM.value
    return IncidentSeverity.LOW.value


def compute_confidence(
    failure_count: int,
    threshold: int,
    sources: list,
) -> int:
    """Compute confidence 0-100 based on failure count and corroboration sources."""
    base = min(40 + (failure_count - threshold) * 5, 70)
    bonus = 0
    if "web" in sources:
        bonus += 10
    if "ids" in sources:
        bonus += 20
    return min(base + bonus, 100)
