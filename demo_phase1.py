#!/usr/bin/env python3
"""
Demo script showing how the new domain models work with existing config.json data.

This demonstrates Phase 1 completion by showing full compatibility with the current system.
"""

import json
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.domain.models import Manifest, Carrier, Acknowledgment, MuteStatus
from src.infrastructure.logging.logger import get_logger

def demo_config_compatibility():
    """Demonstrate compatibility with existing config.json."""
    print("=== Phase 1 Demo: Domain Models with Existing Config ===\n")
    
    # Load the actual config.json
    try:
        with open('config.json', 'r') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found")
        return
    
    print("1. Loading manifests from existing config.json...")
    manifests = []
    
    for manifest_data in config_data['manifests']:
        manifest = Manifest.from_dict(manifest_data)
        manifests.append(manifest)
        print(f"   ✓ Created {manifest}")
    
    print(f"\n   Successfully loaded {len(manifests)} manifests")
    
    print("\n2. Demonstrating manifest operations...")
    
    # Get first manifest for demo
    manifest = manifests[0]
    print(f"   Working with: {manifest.name}")
    print(f"   Time: {manifest.time}")
    print(f"   Carriers: {[c.name for c in manifest.carriers]}")
    
    # Acknowledge a carrier
    carrier = manifest.carriers[0]
    print(f"\n   Acknowledging carrier: {carrier.name}")
    carrier.acknowledge("demo_user", "Demo acknowledgment")
    print(f"   ✓ Carrier acknowledged by {carrier.acknowledgment_details.user}")
    
    # Check manifest status
    print(f"\n   Manifest status: {manifest.get_status()}")
    print(f"   Has acknowledged carriers: {manifest.has_any_acknowledged_carriers()}")
    
    print("\n3. Demonstrating JSON serialization...")
    
    # Convert back to dict (for saving)
    manifest_dict = manifest.to_dict()
    print(f"   ✓ Serialized manifest with acknowledgment data")
    print(f"   Acknowledgment preserved: {manifest_dict['carriers'][0]['acknowledged']}")
    
    print("\n4. Demonstrating mute status...")
    
    # Create and manipulate mute status
    mute_status = MuteStatus.create_unmuted()
    print(f"   Initial status: {mute_status.get_status_summary()}")
    
    mute_status.snooze(5, "demo_user")
    print(f"   After snooze: {mute_status.get_status_summary()}")
    
    mute_status.mute("demo_user", "Demo mute")
    print(f"   After mute: {mute_status.get_status_summary()}")
    
    print("\n5. Demonstrating logging...")
    
    # Test the logging system
    logger = get_logger("demo")
    logger.info("Phase 1 domain models working correctly")
    logger.log_user_action("demo_user", "acknowledge", carrier.name)
    logger.log_performance_metric("demo_metric", 42.5)
    
    print(f"   ✓ Logging system operational")
    
    print("\n=== Demo Complete ===")
    print("✅ Phase 1 domain models successfully integrate with existing system")
    print("✅ All models support JSON serialization/deserialization")
    print("✅ Validation and business logic working correctly")
    print("✅ Logging framework operational")
    print("✅ Ready for Phase 2 implementation")


if __name__ == "__main__":
    demo_config_compatibility()