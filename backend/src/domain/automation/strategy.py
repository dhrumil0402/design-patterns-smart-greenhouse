from abc import ABC, abstractmethod
from dataclasses import dataclass

from domain.automation.context import LocationAutomationContext


@dataclass(frozen=True)
class Recommendation:
    action: str            # "irrigate" | "wait"
    reason: str
    score: float | None = None


class AutomationStrategy(ABC):
    """Strategy interface: every irrigation policy implements decide()."""

    key: str

    @abstractmethod
    def decide(self, context: LocationAutomationContext) -> Recommendation:
        raise NotImplementedError


def _no_sensor() -> Recommendation:
    return Recommendation(action="wait", reason="no moisture sensor in this zone")


class ConservativeMoistureStrategy(AutomationStrategy):
    """Irrigates only once moisture drops below the zone's LOW threshold."""

    key = "conservative"

    def decide(self, context: LocationAutomationContext) -> Recommendation:
        if context.moisture is None:
            return _no_sensor()
        m = context.moisture
        if m < context.moisture_low:
            return Recommendation(
                "irrigate", f"Moisture {m:.2f} is below low threshold {context.moisture_low:.2f}"
            )
        return Recommendation(
            "wait",
            f"Moisture {m:.2f} is not below low threshold {context.moisture_low:.2f}",
        )


class AggressiveMoistureStrategy(AutomationStrategy):
    """Irrigates earlier: as soon as moisture falls below the MIDPOINT of the band."""

    key = "aggressive"

    def decide(self, context: LocationAutomationContext) -> Recommendation:
        if context.moisture is None:
            return _no_sensor()
        m = context.moisture
        midpoint = (context.moisture_low + context.moisture_high) / 2
        if m < midpoint:
            return Recommendation(
                "irrigate", f"Moisture {m:.2f} is below band midpoint {midpoint:.2f}"
            )
        return Recommendation(
            "wait", f"Moisture {m:.2f} is not below band midpoint {midpoint:.2f}"
        )


_STRATEGIES: dict[str, AutomationStrategy] = {
    ConservativeMoistureStrategy.key: ConservativeMoistureStrategy(),
    AggressiveMoistureStrategy.key: AggressiveMoistureStrategy(),
}


def get_strategy(key: str) -> AutomationStrategy:
    """Look up a strategy by key. Unknown key raises ValueError BEFORE decide() runs."""
    try:
        return _STRATEGIES[key]
    except KeyError:
        raise ValueError(f"Unknown automation strategy: {key!r}") from None
