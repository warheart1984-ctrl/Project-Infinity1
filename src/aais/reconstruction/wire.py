"""Strict continuity wire ingestion — maps JSONL records to ContinuityEvent."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.aais.reconstruction.types import ContinuityEvent, META_KINDS

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    Draft202012Validator = None  # type: ignore[misc, assignment]


class WireValidationError(ValueError):
    """Raised when continuity.jsonl violates continuity_wire.v1.json."""


def load_schema(schema_path: Path) -> dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_wire_record(record: dict[str, Any], schema: dict[str, Any]) -> None:
    if Draft202012Validator is None:
        _validate_wire_record_minimal(record)
        return
    validator = Draft202012Validator(schema, format_checker=None)
    errors = sorted(validator.iter_errors(record), key=lambda err: list(err.path))
    if errors:
        detail = "; ".join(error.message for error in errors[:5])
        raise WireValidationError(detail)


def _validate_wire_record_minimal(record: dict[str, Any]) -> None:
    record_type = record.get("record_type")
    if record_type not in {"thread", "event"}:
        raise WireValidationError(f"invalid record_type: {record_type!r}")
    if record_type == "thread":
        if not record.get("thread_id"):
            raise WireValidationError("thread record missing thread_id")
        return
    for key in ("event_id", "thread_id", "type", "timestamp"):
        if key not in record:
            raise WireValidationError(f"event record missing {key}")


def _parse_timestamp(raw: str) -> datetime:
    normalized = raw.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _normalize_kind(raw_kind: str) -> str:
    if raw_kind in META_KINDS:
        return "Meta"
    return raw_kind


def continuity_event_from_wire_record(record: dict[str, Any]) -> ContinuityEvent:
    thread_id = str(record["thread_id"])
    causal = [str(item) for item in (record.get("lineage") or [])]
    if isinstance(record.get("lineage"), dict):
        lineage_obj = dict(record["lineage"])
        causal = [str(item) for item in (lineage_obj.get("causal") or [])]
    else:
        lineage_obj = {"causal": causal, "thread": thread_id}

    parent = record.get("parent_event_id")
    parent_event_id = str(parent) if parent else (causal[0] if causal else None)
    kind = _normalize_kind(str(record.get("kind") or record.get("type")))

    return ContinuityEvent(
        thread_id=thread_id,
        event_id=str(record["event_id"]),
        parent_event_id=parent_event_id,
        timestamp=_parse_timestamp(str(record["timestamp"])),
        kind=kind,
        lineage=lineage_obj,
        payload=dict(record.get("payload") or {}),
    )


def load_wire(
    continuity_wire_path: Path,
    *,
    schema_path: Path,
) -> tuple[list[ContinuityEvent], list[dict[str, Any]], list[dict[str, Any]]]:
    """Load wire; return (events, threads, invalid_findings)."""
    schema = load_schema(schema_path)
    if not continuity_wire_path.exists():
        raise WireValidationError(f"wire file not found: {continuity_wire_path}")

    events: list[ContinuityEvent] = []
    threads: list[dict[str, Any]] = []
    invalid_findings: list[dict[str, Any]] = []

    for line_no, line in enumerate(
        continuity_wire_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        cleaned = line.strip()
        if not cleaned:
            continue
        try:
            record = json.loads(cleaned)
        except json.JSONDecodeError as error:
            invalid_findings.append(
                {
                    "kind": "Error",
                    "code": "INVALID_JSON",
                    "message": f"line {line_no}: {error}",
                    "event_ids": [],
                }
            )
            continue
        if not isinstance(record, dict):
            invalid_findings.append(
                {
                    "kind": "Error",
                    "code": "INVALID_RECORD",
                    "message": f"line {line_no}: record must be object",
                    "event_ids": [],
                }
            )
            continue
        try:
            validate_wire_record(record, schema)
        except WireValidationError as error:
            invalid_findings.append(
                {
                    "kind": "Error",
                    "code": "WIRE_SCHEMA_VIOLATION",
                    "message": f"line {line_no}: {error}",
                    "event_ids": [str(record.get("event_id") or "")] if record.get("event_id") else [],
                }
            )
            continue
        if record.get("record_type") == "thread":
            threads.append(record)
        else:
            events.append(continuity_event_from_wire_record(record))
    return events, threads, invalid_findings


def write_wire_events(
    continuity_wire_path: Path,
    events: list[dict[str, Any]],
    *,
    thread_id: str,
    parent_thread_id: str | None = None,
) -> None:
    continuity_wire_path.parent.mkdir(parents=True, exist_ok=True)
    with continuity_wire_path.open("w", encoding="utf-8") as handle:
        thread_record = {
            "record_type": "thread",
            "thread_id": thread_id,
            "parent_thread_id": parent_thread_id,
            "event_ids": [str(event["event_id"]) for event in events],
        }
        handle.write(json.dumps(thread_record, sort_keys=True) + "\n")
        for event in sorted(events, key=lambda item: item.get("timestamp", "")):
            wire_event = {
                "record_type": "event",
                "event_id": event["event_id"],
                "thread_id": event.get("thread_id", thread_id),
                "type": event["type"],
                "payload": dict(event.get("payload") or {}),
                "timestamp": event["timestamp"],
                "lineage": list(event.get("lineage") or []),
            }
            handle.write(json.dumps(wire_event, sort_keys=True) + "\n")


def write_merged_wire(
    continuity_wire_path: Path,
    segments: list[tuple[str, list[dict[str, Any]], str | None]],
) -> None:
    """Write multiple threads into one continuity.jsonl (FOS cross-thread harness)."""
    continuity_wire_path.parent.mkdir(parents=True, exist_ok=True)
    with continuity_wire_path.open("w", encoding="utf-8") as handle:
        for thread_id, events, parent_thread_id in segments:
            thread_record = {
                "record_type": "thread",
                "thread_id": thread_id,
                "parent_thread_id": parent_thread_id,
                "event_ids": [str(event["event_id"]) for event in events],
            }
            handle.write(json.dumps(thread_record, sort_keys=True) + "\n")
            for event in sorted(events, key=lambda item: item.get("timestamp", "")):
                wire_event = {
                    "record_type": "event",
                    "event_id": event["event_id"],
                    "thread_id": event.get("thread_id", thread_id),
                    "type": event["type"],
                    "payload": dict(event.get("payload") or {}),
                    "timestamp": event["timestamp"],
                    "lineage": list(event.get("lineage") or []),
                }
                handle.write(json.dumps(wire_event, sort_keys=True) + "\n")
