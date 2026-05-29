"""Program debt register surfaced in the operator console."""

from __future__ import annotations

from typing import Any


DEBT_REGISTER: list[dict[str, Any]] = [
    {
        "id": "UGR-D1",
        "item": "Cloud output formats remain stubs",
        "severity": "medium",
        "owner": "operator",
        "status": "open",
        "claim_status": "asserted",
    },
    {
        "id": "UGR-D2",
        "item": "External graph DB at scale (SQLite projection active)",
        "severity": "medium",
        "owner": "architect",
        "status": "partial",
        "claim_status": "asserted",
    },
    {
        "id": "UGR-D3",
        "item": "Governed LLM execution commit",
        "severity": "low",
        "owner": "runtime",
        "status": "closed",
        "claim_status": "proven",
    },
    {
        "id": "UGR-D4",
        "item": "Wolf CoG unified write-path",
        "severity": "high",
        "owner": "runtime",
        "status": "partial",
        "claim_status": "asserted",
    },
    {
        "id": "UGR-D5",
        "item": "Cross-OS trust bundle matrix evidence",
        "severity": "medium",
        "owner": "operator",
        "status": "open",
        "claim_status": "asserted",
    },
    {
        "id": "CF-D5",
        "item": "Cross-machine Cloud Forge latency benchmarks",
        "severity": "medium",
        "owner": "operator",
        "status": "open",
        "claim_status": "asserted",
    },
]


def debt_summary() -> dict[str, Any]:
    open_items = [item for item in DEBT_REGISTER if item.get("status") == "open"]
    partial_items = [item for item in DEBT_REGISTER if item.get("status") == "partial"]
    proven_items = [item for item in DEBT_REGISTER if item.get("claim_status") == "proven"]
    return {
        "total": len(DEBT_REGISTER),
        "open": len(open_items),
        "partial": len(partial_items),
        "proven_claims": len(proven_items),
        "items": list(DEBT_REGISTER),
    }
