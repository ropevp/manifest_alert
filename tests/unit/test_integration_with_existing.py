"""
Test the domain models with the existing config.json structure.
"""

import pytest
from datetime import time
from src.domain.models import Manifest, Carrier
from src.infrastructure.exceptions.custom_exceptions import DataValidationException


def test_manifest_from_config_json_format():
    """Test creating manifests from the current config.json format."""
    # Sample data from the existing config.json
    manifest_data = {
        "time": "07:00",
        "carriers": [
            "Australia Post Metro",
            "EParcel Express",
            "EParcel Postplus"
        ]
    }
    
    manifest = Manifest.from_dict(manifest_data)
    
    assert manifest.name == "Manifest 07:00"  # Default name
    assert manifest.time == time(7, 0)
    assert len(manifest.carriers) == 3
    assert manifest.carriers[0].name == "Australia Post Metro"
    assert manifest.carriers[1].name == "EParcel Express"
    assert manifest.carriers[2].name == "EParcel Postplus"
    assert not manifest.acknowledged
    assert not manifest.missed


def test_manifest_to_dict_compatibility():
    """Test that manifest can be serialized back to compatible format."""
    manifest = Manifest(
        name="Test Manifest",
        time=time(11, 0),
        carriers=[
            Carrier("Test Carrier 1"),
            Carrier("Test Carrier 2")
        ]
    )
    
    data = manifest.to_dict()
    
    assert data['name'] == "Test Manifest"
    assert data['time'] == "11:00"
    assert len(data['carriers']) == 2
    assert data['carriers'][0]['name'] == "Test Carrier 1"
    assert data['carriers'][1]['name'] == "Test Carrier 2"
    assert data['acknowledged'] == False
    assert data['missed'] == False


def test_carrier_creation():
    """Test basic carrier creation."""
    carrier = Carrier("Test Carrier")
    
    assert carrier.name == "Test Carrier"
    assert not carrier.acknowledged
    assert carrier.notes == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])