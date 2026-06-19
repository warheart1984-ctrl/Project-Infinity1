"""Smoke tests for the Lawful Nova Jarvis provider adapter."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

from src.jarvis_protocol import JarvisMessage
from src.providers.nova_lawful_provider import NovaLawfulProvider


@pytest.fixture(autouse=True)
def _nova_env(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("LAWFUL_NOVA_REPO_ROOT", str(repo))
    monkeypatch.setenv("NOVA_LSG_STORE", str(repo / ".runtime" / "test-nova-lsg.jsonl"))
    monkeypatch.setenv("NOVA_CVR_STORE", str(repo / ".runtime" / "test-nova-cvr.jsonl"))


def test_nova_lawful_provider_invoke() -> None:
    provider = NovaLawfulProvider()
    response = asyncio.run(
        provider.invoke(
            [JarvisMessage(role="user", content="observe lawful nova provider smoke")],
            tenant_id="local",
            response_mode="observe",
            routing_profile={"tenant_id": "local"},
        )
    )
    assert response.provider == "nova_lawful"
    assert str(response.content or "").strip()
    assert response.raw and response.raw.get("lawful_turn")
