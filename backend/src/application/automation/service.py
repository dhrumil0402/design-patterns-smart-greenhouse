from __future__ import annotations

from uuid import UUID

from application.automation.dto import RecommendationDto, StrategyReadDto
from application.automation.errors import StrategyNotSetError
from application.locations.errors import NotFoundError
from domain.automation.context import LocationAutomationContext
from domain.automation.strategy import Recommendation, get_strategy


def _combine(results: list[tuple[str, Recommendation]]) -> tuple[str, str]:
    """One action for the whole location: irrigate if ANY zone says irrigate."""
    if not results:
        return "wait", "location has no zones"
    irrigating = [(name, rec) for name, rec in results if rec.action == "irrigate"]
    chosen = irrigating or results
    action = "irrigate" if irrigating else "wait"
    reason = "; ".join(f"{name}: {rec.reason}" for name, rec in chosen)
    return action, reason


class AutomationService:
    """Chooses and runs a strategy. The strategies themselves never touch the database."""

    def __init__(self, locations, rules) -> None:
        self._locations = locations  # LocationRepository: location_exists, list_zones
        self._rules = rules          # AutomationRepository: saved key + latest moisture

    def set_strategy(self, location_id: UUID, strategy_key: str) -> StrategyReadDto:
        if not self._locations.location_exists(location_id):
            raise NotFoundError("location not found")
        get_strategy(strategy_key)  # unknown key -> ValueError, so nothing is saved
        self._rules.upsert_strategy_key(location_id, strategy_key)
        return StrategyReadDto(location_id=location_id, strategy_key=strategy_key)

    def evaluate(self, location_id: UUID) -> RecommendationDto:
        if not self._locations.location_exists(location_id):
            raise NotFoundError("location not found")

        key = self._rules.get_strategy_key(location_id)  # the PERSISTED key, not the request's
        if key is None:
            raise StrategyNotSetError("no strategy saved for this location; save one first")
        strategy = get_strategy(key)

        zones = self._locations.list_zones(location_id)
        moisture = self._rules.latest_moisture_by_zone([zone.id for zone in zones])

        results: list[tuple[str, Recommendation]] = []
        for zone in zones:
            context = LocationAutomationContext(
                location_id=location_id,
                zone_id=zone.id,
                moisture=moisture.get(zone.id),  # None when the zone has no moisture sensor
                moisture_low=zone.moisture_threshold_low,
                moisture_high=zone.moisture_threshold_high,
            )
            results.append((zone.name, strategy.decide(context)))

        action, reason = _combine(results)
        return RecommendationDto(
            location_id=location_id, strategy_key=key, action=action, reason=reason
        )
