"""Quick check for time-based flight nudges."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.orchestrator import _build_time_nudges, _find_flight_record  # noqa: E402


def test_time_nudges_for_ai143() -> None:
    flight = _find_flight_record("AI 143", {})
    assert flight is not None

    message, nudges = _build_time_nudges(flight)

    assert "Head to security" in message
    assert "Go to gate" in message
    assert "Final call" in message
    assert len(nudges) == 3
    assert nudges[0]["time"] == "09:20"
    assert nudges[1]["time"] == "10:35"
    assert nudges[2]["time"] == "11:10"


if __name__ == "__main__":
    test_time_nudges_for_ai143()
    print("time-based nudges ok")