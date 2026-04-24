"""Health compatibility tests for the canonical FastAPI app."""

from __future__ import annotations

import types
import unittest
from unittest.mock import patch

from app import main as app_main


class TestCanonicalHealth(unittest.TestCase):
    def test_legacy_bridge_mount_uses_supported_a2wsgi_wrapper(self):
        mounted_route = next(
            route for route in app_main.app.routes if getattr(route, "path", None) == app_main.LEGACY_API_MOUNT_PATH
        )

        self.assertEqual(mounted_route.app.__class__.__name__, "WSGIMiddleware")
        self.assertTrue(mounted_route.app.__class__.__module__.startswith("a2wsgi"))

    def test_build_operator_health_payload_uses_legacy_runtime_snapshot(self):
        bootstrap_calls: list[str] = []

        fake_legacy_api = types.SimpleNamespace(
            bootstrap_ai_runtime=lambda reason="startup": bootstrap_calls.append(reason),
            _build_ai_runtime_status=lambda: {
                "requested_model_mode": "real",
                "active_model_mode": "real",
                "ai_status": "initialized",
                "ai_bootstrap_status": "initialized",
                "ai_bootstrap_reason": "run_api",
                "ai_fallback_active": False,
            },
            system_guard=types.SimpleNamespace(snapshot=lambda limit_events=4: {"status": "nominal"}),
            dreamspace=types.SimpleNamespace(snapshot=lambda limit_dreams=2: {"status": "stopped"}),
        )

        with patch("app.main.importlib.import_module", return_value=fake_legacy_api):
            payload = app_main._build_operator_health_payload()

        self.assertEqual(payload["status"], "healthy")
        self.assertEqual(payload["service"], "AAIS Multi-Modal AI")
        self.assertEqual(payload["active_model_mode"], "real")
        self.assertEqual(payload["ai_status"], "initialized")
        self.assertEqual(bootstrap_calls, ["canonical_health"])
        self.assertIn("system_guard", payload)
        self.assertIn("dreamspace", payload)

    def test_build_operator_health_payload_degrades_cleanly_when_legacy_runtime_is_unavailable(self):
        with patch("app.main.importlib.import_module", side_effect=RuntimeError("legacy bridge unavailable")):
            payload = app_main._build_operator_health_payload()

        self.assertEqual(payload["status"], "degraded")
        self.assertEqual(payload["service"], "AAIS Workflow Shell")
        self.assertEqual(payload["ai_status"], "not_initialized")
        self.assertIn("legacy bridge unavailable", payload["ai_init_error"])


if __name__ == "__main__":
    unittest.main()
