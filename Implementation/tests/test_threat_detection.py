#!/usr/bin/env python3
"""
Unit tests for rules-based threat detection.

Run from the project root:
  python -m unittest tests.test_threat_detection
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from api.threat_detection import ThreatDetector


class TestThreatDetection(unittest.TestCase):
    """Test suite covering core ThreatDetector rules."""

    def setUp(self):
        """Create a detector with deterministic thresholds for tests."""
        self.detector = ThreatDetector(
            failed_attempt_threshold=3,
            failed_attempt_window_minutes=10,
            inactivity_threshold_hours=24,
        )

    def test_repeated_failed_access_triggers(self):
        """Repeated failed attempts within window should trigger HIGH threat."""
        person_id = "resident_123"
        now = datetime.now()
        self.detector.failed_attempts.extend(
            [
                (now - timedelta(minutes=1), person_id),
                (now - timedelta(minutes=2), person_id),
                (now - timedelta(minutes=3), person_id),
            ]
        )
        threat = self.detector.check_failed_access_attempts(person_id)
        self.assertIsNotNone(threat)
        self.assertEqual(threat.get("threat_type"), "REPEATED_FAILED_ACCESS")
        self.assertEqual(threat.get("severity"), "HIGH")

    def test_repeated_failed_access_no_trigger(self):
        """Under-threshold failed attempts should not trigger a threat."""
        person_id = "resident_123"
        now = datetime.now()
        self.detector.failed_attempts.extend(
            [
                (now - timedelta(minutes=1), person_id),
                (now - timedelta(minutes=2), person_id),
            ]
        )
        threat = self.detector.check_failed_access_attempts(person_id)
        self.assertIsNone(threat)

    def test_inactivity_triggers(self):
        """Inactivity beyond threshold should trigger CRITICAL alert."""
        person_id = "resident_123"
        last_activity = datetime.now() - timedelta(hours=25)
        threat = self.detector.check_inactivity(person_id, last_activity)
        self.assertIsNotNone(threat)
        self.assertEqual(threat.get("threat_type"), "PROLONGED_INACTIVITY")
        self.assertEqual(threat.get("severity"), "CRITICAL")

    @patch("api.threat_detection.datetime")
    def test_wandering_triggers_on_night_exit(self, mock_dt):
        """Night-time exit should trigger wandering HIGH threat."""
        mock_dt.now.return_value = datetime(2026, 1, 1, 23, 0, 0)
        threat = self.detector.check_wandering("resident_123", "exit")
        self.assertIsNotNone(threat)
        self.assertEqual(threat.get("threat_type"), "WANDERING_DETECTED")
        self.assertEqual(threat.get("severity"), "HIGH")
        self.assertEqual(threat.get("access_hour"), 23)

    def test_wandering_no_trigger_on_entry(self):
        """Night-time entry should not trigger wandering (only exits)."""
        with patch("api.threat_detection.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 1, 23, 0, 0)
            threat = self.detector.check_wandering("resident_123", "entry")
            self.assertIsNone(threat)

    def test_tailgating_triggers_on_rapid_multi_entry(self):
        """Two different users entering within 15 seconds should trigger tailgating."""
        now_utc = datetime.utcnow()
        db = MagicMock()
        db.get_access_logs.return_value = [
            {
                "user_id": "resident_A",
                "type": "entry",
                "status": "success",
                "confidence": 0.95,
                "timestamp": (now_utc - timedelta(seconds=5)).isoformat(),
            },
            {
                "user_id": "resident_B",
                "type": "entry",
                "status": "success",
                "confidence": 0.93,
                "timestamp": (now_utc - timedelta(seconds=10)).isoformat(),
            },
        ]
        threat = self.detector.check_tailgating("resident_A", db)
        self.assertIsNotNone(threat)
        self.assertEqual(threat.get("threat_type"), "TAILGATING_DETECTED")
        self.assertEqual(threat.get("severity"), "HIGH")

    def test_tailgating_no_trigger_same_user(self):
        """Same user multiple times should not trigger tailgating."""
        now_utc = datetime.utcnow()
        db = MagicMock()
        db.get_access_logs.return_value = [
            {
                "user_id": "resident_A",
                "type": "entry",
                "status": "success",
                "confidence": 0.95,
                "timestamp": (now_utc - timedelta(seconds=5)).isoformat(),
            },
            {
                "user_id": "resident_A",
                "type": "entry",
                "status": "success",
                "confidence": 0.93,
                "timestamp": (now_utc - timedelta(seconds=10)).isoformat(),
            },
        ]
        threat = self.detector.check_tailgating("resident_A", db)
        self.assertIsNone(threat)

    @patch("api.threat_detection.datetime")
    def test_unusual_access_time_triggers_at_night(self, mock_dt):
        """Night-time access should trigger MEDIUM unusual-access-time alert."""
        mock_dt.now.return_value = datetime(2026, 1, 1, 23, 0, 0)
        threat = self.detector.check_unusual_access_time("resident_123")
        self.assertIsNotNone(threat)
        self.assertEqual(threat.get("threat_type"), "UNUSUAL_ACCESS_TIME")
        self.assertEqual(threat.get("severity"), "MEDIUM")

    def test_frequency_spike_triggers(self):
        """Excessive access events in a window should trigger frequency spike alert."""
        person_id = "resident_123"
        now = datetime.now()
        self.detector.access_log.extend(
            [(now - timedelta(minutes=1), person_id, "success")] * 11
        )
        threat = self.detector.check_frequency_spike(
            person_id, window_minutes=60, spike_threshold=10
        )
        self.assertIsNotNone(threat)
        self.assertEqual(threat.get("threat_type"), "ACCESS_FREQUENCY_SPIKE")
        self.assertEqual(threat.get("severity"), "MEDIUM")


if __name__ == "__main__":
    unittest.main()

