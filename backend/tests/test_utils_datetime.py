"""Unit tests for date and time utilities."""

from app.utils.datetime import duration


class TestDuration:
    def test_default(self):
        assert duration(3723000) == "01:02:03"

    def test_seconds(self):
        assert duration(125, "seconds") == "02:05"
