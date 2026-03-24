#!/usr/bin/env python3
"""
Unit tests for fall detection routes and repeated-falls logic.

Run:
  python -m unittest tests.test_fall_detection
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from flask import Flask

from api.fall_detection_routes import fall_bp, _build_fall_description
from api.threat_detection import ThreatDetector


class TestFallHelpers(unittest.TestCase):
    def test_build_fall_description_includes_source(self):
        text = _build_fall_description(
            reason="rapid drop",
            confidence=0.91,
            hip_height=0.77,
            torso_angle=67.1,
            hip_velocity=0.12,
            source="lstm",
        )
        self.assertIn("source=lstm", text)
        self.assertIn("confidence=0.91", text)


class TestRepeatedFallsRule(unittest.TestCase):
    def test_repeated_falls_warns_at_two(self):
        detector = ThreatDetector()
        now = datetime.now()
        db = MagicMock()
        db.get_anomalies.return_value = [
            {"timestamp": (now - timedelta(hours=1)).isoformat(), "anomaly_type": "fall_detected"},
            {"timestamp": (now - timedelta(hours=2)).isoformat(), "anomaly_type": "fall_detected"},
        ]
        alert = detector.check_repeated_falls(db)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.get("threat_type"), "REPEATED_FALLS_WARNING")
        self.assertEqual(alert.get("severity"), "HIGH")


class TestFallLogRoute(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(fall_bp, url_prefix="/api/fall")
        app.db = MagicMock()
        app.threat_detector = ThreatDetector()
        app.fall_detector = None
        app.fall_detector_mode = "rules"
        app.fall_detector_mode_requested = "rules"
        app.fall_model_artifacts = {}
        app.fall_model_info = {}
        self.client = app.test_client()

    def test_log_fall_requires_confidence(self):
        resp = self.client.post("/api/fall/log", json={"reason": "test"})
        self.assertEqual(resp.status_code, 400)

    def test_log_fall_logs_anomaly_and_threat(self):
        resp = self.client.post(
            "/api/fall/log",
            json={
                "confidence": 0.82,
                "reason": "test fall",
                "hip_height": 0.8,
                "torso_angle_deg": 62.0,
                "hip_velocity": 0.09,
                "detector_source": "lstm",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.client.application.db.log_anomaly.called)
        self.assertTrue(self.client.application.db.log_threat.called)

    def test_visibility_warning_does_not_log_fall_anomaly(self):
        resp = self.client.post(
            "/api/fall/log",
            json={
                "confidence": 0.0,
                "reason": "Body not fully visible — move back from camera",
                "detector_source": "lstm",
            },
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertEqual(payload.get("status"), "logged_warning")
        self.assertFalse(self.client.application.db.log_anomaly.called)
        self.assertTrue(self.client.application.db.log_threat.called)


if __name__ == "__main__":
    unittest.main()
