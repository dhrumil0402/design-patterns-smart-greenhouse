from abc import ABC, abstractmethod

from domain.devices.entity import Device
from domain.sensors.creators import MoistureSensorCreator, LightSensorCreator


class DeviceFamilyFactory(ABC):
    @property
    @abstractmethod
    def family_key(self) -> str: ...

    @abstractmethod
    def create_device_set(self) -> list[Device]: ...


class SimulationDeviceFactory(DeviceFamilyFactory):
    @property
    def family_key(self) -> str:
        return "simulation"

    def create_device_set(self) -> list[Device]:
        moisture = MoistureSensorCreator().create_sensor(display_name="Sim moisture sensor")
        light = LightSensorCreator().create_sensor(display_name="Sim light sensor")

        return [
            Device(
                id=None,
                device_type=moisture.device_type,
                role="sensor",
                device_family=self.family_key,
                display_name=moisture.display_name,
                default_config={**moisture.default_config, "protocol": "simulation"},
                sampling_interval_seconds=moisture.default_config["sampling_interval_seconds"],
            ),
            Device(
                id=None,
                device_type=light.device_type,
                role="sensor",
                device_family=self.family_key,
                display_name=light.display_name,
                default_config={**light.default_config, "protocol": "simulation"},
                sampling_interval_seconds=light.default_config["sampling_interval_seconds"],
            ),
            Device(
                id=None,
                device_type="water_pump",
                role="actuator",
                device_family=self.family_key,
                display_name="Sim irrigation pump",
                default_config={"protocol": "sim"},
            ),
            Device(
                id=None,
                device_type="grow_light",
                role="actuator",
                device_family=self.family_key,
                display_name="Sim grow light",
                default_config={"protocol": "sim"},
            ),
        ]


class EdgeHardwareFactory(DeviceFamilyFactory):
    @property
    def family_key(self) -> str:
        return "edge"

    def create_device_set(self) -> list[Device]:
        moisture = MoistureSensorCreator().create_sensor(display_name="Edge moisture probe")
        light = LightSensorCreator().create_sensor(display_name="Edge light probe")

        return [
            Device(
                id=None,
                device_type=moisture.device_type,
                role="sensor",
                device_family=self.family_key,
                display_name=moisture.display_name,
                default_config={**moisture.default_config, "protocol": "mqtt"},
                sampling_interval_seconds=moisture.default_config["sampling_interval_seconds"],
            ),
            Device(
                id=None,
                device_type=light.device_type,
                role="sensor",
                device_family=self.family_key,
                display_name=light.display_name,
                default_config={**light.default_config, "protocol": "mqtt"},
                sampling_interval_seconds=light.default_config["sampling_interval_seconds"],
            ),
            Device(
                id=None,
                device_type="water_pump",
                role="actuator",
                device_family=self.family_key,
                display_name="Edge irrigation pump",
                default_config={"protocol": "gpio-stub"},
            ),
            Device(
                id=None,
                device_type="grow_light",
                role="actuator",
                device_family=self.family_key,
                display_name="Edge grow light",
                default_config={"protocol": "gpio-stub"},
            ),
        ]


_FACTORIES: dict[str, type[DeviceFamilyFactory]] = {
    "simulation": SimulationDeviceFactory,
    "edge": EdgeHardwareFactory,
}


def get_family_factory(family: str) -> DeviceFamilyFactory:
    factory_cls = _FACTORIES.get(family)
    if factory_cls is None:
        raise ValueError(f"unknown device family: {family}")
    return factory_cls()