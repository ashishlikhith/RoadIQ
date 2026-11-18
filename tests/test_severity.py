"""
RoadIQ Severity Estimation & Municipal Triage Unit Tests
Verifies mathematical formulation S = clip(round(0.15 * D + 2.0 * R), 1, 5),
depth proxy calibration, and municipal SLA priority mappings.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from severity import calculate_severity, get_severity_info, SEVERITY_MAPPING

class TestSeverityCalculation:
    """Test mathematical bounds, clipping, and depth proxy calculation"""

    def test_lower_bound_clipping(self):
        """Minimum severity must be clipped to 1 even with 0 or negative inputs"""
        score, label, action, flagged, depth = calculate_severity(d_mm=0.0, r_mm_ms=0.0)
        assert score == 1
        assert label == "Minor"
        assert flagged is False
        assert depth >= 1.0

    def test_upper_bound_clipping(self):
        """Maximum severity must be clipped to 5 for massive potholes"""
        score, label, action, flagged, depth = calculate_severity(d_mm=50.0, r_mm_ms=5.0)
        assert score == 5
        assert label == "Critical"
        assert flagged is True

    def test_critical_severity_threshold(self):
        """Verify severity 5 threshold (e.g. D=24.0mm, R=1.8mm/ms)"""
        # raw = 0.15 * 24.0 + 2.0 * 1.8 = 3.6 + 3.6 = 7.2 -> round = 7 -> clip = 5
        score, label, action, flagged, depth = calculate_severity(d_mm=24.0, r_mm_ms=1.8)
        assert score == 5
        assert label == "Critical"
        assert flagged is True
        assert depth > 5.0

    def test_high_severity_threshold(self):
        """Verify severity 4 threshold (e.g. D=18.0mm, R=1.2mm/ms)"""
        # raw = 0.15 * 18.0 + 2.0 * 1.2 = 2.7 + 2.4 = 5.1 -> round = 5 -> clip = 5
        score, label, action, flagged, depth = calculate_severity(d_mm=18.0, r_mm_ms=0.6)
        # raw = 2.7 + 1.2 = 3.9 -> round = 4
        assert score == 4
        assert label == "High"
        assert flagged is True

    def test_depth_proxy_formula(self):
        """Depth proxy must follow calibrated OLS: depth = round(max(1.0, 0.22*D + 0.5*R), 1)"""
        d = 20.0
        r = 1.4
        expected_depth = round(max(1.0, 0.22 * d + 0.5 * r), 1)
        _, _, _, _, depth = calculate_severity(d, r)
        assert depth == expected_depth

class TestSeverityMetadata:
    """Test municipal SLA mappings and color codes"""

    def test_all_severity_levels_defined(self):
        for s in range(1, 6):
            info = get_severity_info(s)
            assert "label" in info
            assert "action" in info
            assert "badge_color" in info
            assert "flagged" in info
            assert "sla_hours" in info

    def test_critical_sla_is_24_hours(self):
        info = get_severity_info(5)
        assert info["sla_hours"] == 24
        assert info["flagged"] is True

    def test_high_sla_is_48_hours(self):
        info = get_severity_info(4)
        assert info["sla_hours"] == 48
        assert info["flagged"] is True
