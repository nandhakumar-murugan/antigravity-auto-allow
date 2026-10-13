"""
Unit tests for Antigravity Auto-Allow coordinate calculations and logic.
"""

import pytest


def test_bounding_box_subdivision():
    """Verify calculation of lower-half bounding box region for targeted dialog detection."""
    left, top, right, bottom = 100, 100, 900, 700
    width = right - left
    height = bottom - top

    # Lower half region
    lower_top = top + int(height * 0.5)
    lower_height = bottom - lower_top

    assert width == 800
    assert height == 600
    assert lower_top == 400
    assert lower_height == 300


def test_target_coordinate_clamping():
    """Ensure coordinates stay clamped inside application window boundaries."""
    window_bounds = (50, 50, 850, 650)
    test_clicks = [
        (450, 600, True),
        (20, 600, False),
        (500, 700, False),
        (50, 50, True),
        (850, 650, True),
    ]

    for x, y, expected in test_clicks:
        is_inside = (
            window_bounds[0] <= x <= window_bounds[2] and
            window_bounds[1] <= y <= window_bounds[3]
        )
        assert is_inside == expected


def test_color_match_tolerance():
    """Verify RGB tolerance check for the Antigravity submit button accent."""
    target_blue = (26, 115, 232)  # Google blue
    tolerance = 25

    def matches_accent(rgb):
        return all(abs(c - t) <= tolerance for c, t in zip(rgb, target_blue))

    assert matches_accent((26, 115, 232)) is True
    assert matches_accent((30, 110, 240)) is True
    assert matches_accent((255, 255, 255)) is False
    assert matches_accent((30, 31, 34)) is False
