from domain.sensors.creators import (
    LightSensorCreator,
    MoistureSensorCreator,
    get_creator,
)


def test_moisture_creator_has_moisture_related_defaults():
    sensor = MoistureSensorCreator().create_sensor()
    assert sensor.device_type == "moisture_sensor"
    assert "moisture_threshold_percent" in sensor.default_config
    assert sensor.default_config["unit"] == "vwc"


def test_light_creator_uses_different_unit_and_type():
    sensor = LightSensorCreator().create_sensor()
    assert sensor.device_type == "light_sensor"
    assert sensor.default_config["unit"] == "lux"
    assert "moisture_threshold_percent" not in sensor.default_config


def test_moisture_and_light_defaults_are_distinct():
    moisture = MoistureSensorCreator().create_sensor()
    light = LightSensorCreator().create_sensor()
    assert moisture.default_config != light.default_config
    assert moisture.device_type != light.device_type


def test_get_creator_returns_correct_creator_for_known_types():
    assert isinstance(get_creator("moisture"), MoistureSensorCreator)
    assert isinstance(get_creator("light"), LightSensorCreator)


def test_get_creator_raises_on_unknown_type():
    try:
        get_creator("temperature")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "temperature" in str(exc)


def test_custom_display_name_is_used_when_provided():
    sensor = MoistureSensorCreator().create_sensor(display_name="Bed 3")
    assert sensor.display_name == "Bed 3"


def test_default_display_name_used_when_not_provided():
    sensor = LightSensorCreator().create_sensor()
    assert sensor.display_name == "Light sensor"
