from domain.devices.family_factory import SimulationDeviceFactory, EdgeHardwareFactory


def test_simulation_factory_returns_four_devices():
    devices = SimulationDeviceFactory().create_device_set()
    assert len(devices) == 4
    roles = {d.role for d in devices}
    assert roles == {"sensor", "actuator"}
    assert all(d.device_family == "simulation" for d in devices)


def test_edge_factory_differs_from_simulation():
    sim = SimulationDeviceFactory().create_device_set()
    edge = EdgeHardwareFactory().create_device_set()
    sim_protocols = {d.default_config.get("protocol") for d in sim}
    edge_protocols = {d.default_config.get("protocol") for d in edge}
    assert sim_protocols != edge_protocols