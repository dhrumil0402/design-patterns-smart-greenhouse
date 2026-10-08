import pytest

from domain.locations.config_builder import LocationConfigBuilder
from domain.locations.errors import ConfigurationError


def test_build_success():
    config = (
        LocationConfigBuilder()
        .with_location_name("Lab Site A")
        .add_zone("Bench 1", 0.2, 0.45)
        .build()
    )
    assert config.location.name == "Lab Site A"
    assert len(config.location.zones) == 1
    assert config.location.zones[0].name == "Bench 1"


def test_build_requires_name():
    with pytest.raises(ConfigurationError):
        LocationConfigBuilder().add_zone("Bench 1", 0.2, 0.45).build()


def test_build_requires_zones():
    with pytest.raises(ConfigurationError):
        LocationConfigBuilder().with_location_name("Lab Site A").build()


def test_build_rejects_invalid_threshold_order():
    with pytest.raises(ConfigurationError):
        (
            LocationConfigBuilder()
            .with_location_name("Lab Site A")
            .add_zone("Bench 1", 0.5, 0.3)  # low >= high
            .build()
        )


def test_build_rejects_out_of_range_threshold():
    with pytest.raises(ConfigurationError):
        (
            LocationConfigBuilder()
            .with_location_name("Lab Site A")
            .add_zone("Bench 1", -0.1, 0.5)  # below 0.0
            .build()
        )


def test_build_supports_multiple_zones():
    config = (
        LocationConfigBuilder()
        .with_location_name("Lab Site A")
        .add_zone("Bench 1", 0.2, 0.45)
        .add_zone("Bench 2", 0.15, 0.35)
        .build()
    )
    assert len(config.location.zones) == 2

def test_build_rejects_duplicate_zone_names():
    with pytest.raises(ConfigurationError):
        (
            LocationConfigBuilder()
            .with_location_name("Lab Site A")
            .add_zone("Bench 1", 0.2, 0.45)
            .add_zone("bench 1 ", 0.15, 0.35)  # same name, different case and spacing
            .build()
        )


def test_same_zone_name_is_allowed_in_different_locations():
    for site in ("Lab Site A", "Lab Site B"):
        config = (
            LocationConfigBuilder()
            .with_location_name(site)
            .add_zone("Bench 1", 0.2, 0.45)
            .build()
        )
        assert config.location.zones[0].name == "Bench 1"