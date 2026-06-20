"""NeoMundi measurement types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NeoMundiMeasurement:
    measurement_id: str
    signal_type: str
    payload: dict[str, Any]
    timestamp: str
    integrity: str = "asserted"
    source: str = "neomundi.local"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "measurement_id": self.measurement_id,
            "signal_type": self.signal_type,
            "payload": dict(self.payload),
            "timestamp": self.timestamp,
            "integrity": self.integrity,
            "source": self.source,
            "tags": list(self.tags),
        }
