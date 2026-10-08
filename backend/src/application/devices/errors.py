class AssignmentNotFoundError(LookupError):
    """A device, zone, or zone-in-location lookup failed (maps to HTTP 404)."""