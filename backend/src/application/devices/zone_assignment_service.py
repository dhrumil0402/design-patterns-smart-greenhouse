import uuid

from application.devices.errors import AssignmentNotFoundError
from domain.devices.entity import Device
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.location_repository import LocationRepository


class ZoneAssignmentService:
    def __init__(self, devices: DeviceRepository, locations: LocationRepository) -> None:
        self._devices = devices
        self._locations = locations

    def assign(self, device_id: uuid.UUID, zone_id: uuid.UUID | None) -> Device:
        if zone_id is None:
            zone_id_to_set, location_id = None, None
        else:
            location_id = self._locations.get_zone_location_id(zone_id)
            if location_id is None:
                raise AssignmentNotFoundError("zone not found")
            zone_id_to_set = zone_id

        device = self._devices.set_assignment(device_id, zone_id_to_set, location_id)
        if device is None:
            raise AssignmentNotFoundError("device not found")
        return device

    def list_devices(self, location_id: uuid.UUID, zone_id: uuid.UUID) -> list[Device]:
        if self._locations.get_zone_location_id(zone_id) != location_id:
            raise AssignmentNotFoundError("zone not found in this location")
        return self._devices.list_devices_in_zone(zone_id)