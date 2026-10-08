class StrategyNotSetError(ValueError):
    """Evaluate was called before any strategy was saved for the location (maps to HTTP 400)."""
