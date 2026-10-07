from uuid import uuid4

import pytest

from domain.automation.context import LocationAutomationContext
from domain.automation.strategy import get_strategy


def ctx(moisture):
    return LocationAutomationContext(
        location_id=uuid4(), zone_id=uuid4(),
        moisture=moisture, moisture_low=0.25, moisture_high=0.45,
    )


def test_conservative_waits_when_within_band():
    r = get_strategy("conservative").decide(ctx(0.40))
    assert r.action == "wait"


def test_aggressive_differs_on_same_context():
    same = ctx(0.30)  # inside the band, but below the midpoint 0.35
    assert get_strategy("conservative").decide(same).action == "wait"
    assert get_strategy("aggressive").decide(same).action == "irrigate"


def test_both_irrigate_when_below_low():
    c = ctx(0.10)
    assert get_strategy("conservative").decide(c).action == "irrigate"
    assert get_strategy("aggressive").decide(c).action == "irrigate"


def test_zone_without_sensor_waits():
    r = get_strategy("aggressive").decide(ctx(None))
    assert r.action == "wait" and "no moisture sensor" in r.reason


def test_unknown_strategy_key_is_rejected():
    with pytest.raises(ValueError):
        get_strategy("yolo")
