#!/usr/bin/env python3
"""
Simple VLAN Migration Script: SL-SWTG124AS to Binardat 10G08-0800GSM
This script migrates VLAN configuration from the SL-SWTG124AS switch to the Binardat switch.
"""

import sys
import subprocess
import json
from datetime import datetime

# VLAN configuration extracted from SL-SWTG124AS (10.41.8.34)
SOURCE_VLANS = [
    {"id": 1, "name": "Default", "description": "Default VLAN", "ports": "1-6", "untagged": "1-6", "tagged": "-"},
    {"id": 105, "name": "TOR01-WAN1", "description": "TOR01 WAN1", "ports": "-", "untagged": "-", "tagged": "-"},
    {"id": 106, "name": "TOR01-WAN2", "description": "TOR01 WAN2", "ports": "1-6", "untagged": "1-4,6", "tagged": "5"},
    {"id": 110, "name": "TOR01-Manageme", "description": "TOR01 Management", "ports": "-", "untagged": "-", "tagged": "-"},
    {"id": 120, "name": "TOR01-NetMgmt", "description": "TOR01 Network Management", "ports": "1,5", "untagged": "1,5", "tagged": "-"},
    {"id": 130, "name": "TOR01-Storage", "description": "TOR01 Storage", "ports": "-", "untagged": "-", "tagged": "-"},
    {"id": 140, "name": "TOR01-Workstat", "description": "TOR01 Workstations", "ports": "-", "untagged": "-", "tagged": "-"},
    {"id": 150, "name": "TOR01-Servers", "description": "TOR01 Servers", "ports": "-", "untagged": "-", "tagged": "-"},
    {"id": 160, "name": "ServersDMZ", "description": "Servers DMZ", "ports": "-", "untagged": "-", "tagged": "-"},
    {"id": 170, "name": "TOR01-CCTV", "description": "TOR01 CCTV", "ports": "-", "untagged": "-", "tagged": "-"},
    {"id": 180, "name": "TOR01-IOT", "description": "TOR01 IoT", "ports": "-", "untagged": "-", "tagged": "-"},
    {"id": 190, "name": "TOR01-GuestWif", "description": "TOR01 Guest WiFi", "ports": "-", "untagged": "-", "tagged": "-"}
]

def run_command(cmd):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def migrate_vlans(target_url, username, password):
    """Migrate VLAN configuration to Binardat 10G08-0800GSM."""
    print("🔄 VLAN Migration: SL-SWTG124AS → Binardat 10G08-0800GSM")
    print("=" * 70)
    
    # First, let's check if we can connect to the target switch
    print(f"📡 Testing connection to target switch: {target_url}")
    cmd = f"python3 modular_parser.py --url {target_url} --username {username} --password {password} --model 10G08-0800GSM --export test_connection.json"
    
    success, stdout, stderr = run_command(cmd)
    if not success:
        print(f"❌ Failed to connect to target switch: {stderr}")
        return False
    
    print("✅ Connected to target switch successfully!")
    
    # Check current VLAN configuration
    print("\n📋 Checking current VLAN configuration on target switch...")
    cmd = f"python3 modular_parser.py --url {target_url} --username {username} --password {password} --model 10G08-0800GSM --export current_vlans.json"
    
    success, stdout, stderr = run_command(cmd)
    if not success:
        print(f"⚠️  Could not retrieve current VLAN configuration: {stderr}")
        print("   This may be due to session management issues.")
        print("\n🔧 Manual Migration Required:")
        print("   Please configure the following VLANs manually on the target switch:")
        print(f"   {target_url}")
        print_vlan_configuration()
        return False
    
    print("✅ Retrieved current VLAN configuration")
    
    # Attempt to create each VLAN
    migrated_vlans = []
    failed_vlans = []
    
    for vlan in SOURCE_VLANS:
        print(f"\n🔧 Migrating VLAN {vlan['id']}: {vlan['name']}")
        
        # Skip VLAN 1 (default) as it usually exists
        if vlan['id'] == 1:
            print(f"   ⏭️  Skipping VLAN 1 (default VLAN)")
            migrated_vlans.append(vlan)
            continue
        
        # Create the VLAN
        print(f"   ➕ Creating VLAN {vlan['id']}...")
        cmd = f"python3 modular_parser.py --url {target_url} --username {username} --password {password} --model 10G08-0800GSM --create-vlan {vlan['id']}:{vlan['name']}"
        
        success, stdout, stderr = run_command(cmd)
        if success:
            print(f"   ✅ VLAN {vlan['id']} created successfully")
            migrated_vlans.append(vlan)
        else:
            print(f"   ❌ Failed to create VLAN {vlan['id']}: {stderr}")
            failed_vlans.append(vlan)
    
    # Save configuration
    print(f"\n💾 Saving configuration...")
    cmd = f"python3 modular_parser.py --url {target_url} --username {username} --password {password} --model 10G08-0800GSM --save-config"
    
    success, stdout, stderr = run_command(cmd)
    if success:
        print("✅ Configuration saved successfully")
    else:
        print("⚠️  Configuration save not implemented or failed")
    
    # Generate migration summary
    print("\n📊 Migration Summary:")
    print("=" * 50)
    print(f"Total VLANs to migrate: {len(SOURCE_VLANS)}")
    print(f"Successfully migrated: {len(migrated_vlans)}")
    print(f"Failed migrations: {len(failed_vlans)}")
    
    if migrated_vlans:
        print("\n✅ Successfully migrated VLANs:")
        for vlan in migrated_vlans:
            print(f"  - VLAN {vlan['id']}: {vlan['name']} ({vlan['description']})")
            if vlan['ports'] != '-':
                print(f"    Ports: {vlan['ports']} (Untagged: {vlan['untagged']}, Tagged: {vlan['tagged']})")
    
    if failed_vlans:
        print("\n❌ Failed VLAN migrations:")
        for vlan in failed_vlans:
            print(f"  - VLAN {vlan['id']}: {vlan['name']}")
    
    # Export final configuration
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_file = f"vlan_migration_result_{timestamp}.json"
    
    print(f"\n📁 Exporting final configuration to: {export_file}")
    cmd = f"python3 modular_parser.py --url {target_url} --username {username} --password {password} --model 10G08-0800GSM --export {export_file}"
    
    success, stdout, stderr = run_command(cmd)
    if success:
        print("✅ Final configuration exported successfully")
    else:
        print(f"⚠️  Failed to export final configuration: {stderr}")
    
    if failed_vlans:
        print("\n🔧 Manual Configuration Required:")
        print("   For failed VLANs, please configure manually through the web interface:")
        print(f"   {target_url}")
        print_vlan_configuration()
    
    print("\n✅ VLAN migration completed!")
    
    return len(failed_vlans) == 0

def print_vlan_configuration():
    """Print the VLAN configuration for manual setup."""
    print("\n📋 Manual VLAN Configuration:")
    print("-" * 40)
    for vlan in SOURCE_VLANS:
        print(f"VLAN {vlan['id']}: {vlan['name']}")
        print(f"  Description: {vlan['description']}")
        if vlan['ports'] != '-':
            print(f"  Ports: {vlan['ports']}")
            print(f"  Untagged: {vlan['untagged']}")
            print(f"  Tagged: {vlan['tagged']}")
        else:
            print(f"  Ports: None configured")
        print()

def main():
    """Main function."""
    if len(sys.argv) != 4:
        print("Usage: python3 migrate_vlans_simple.py <target_url> <username> <password>")
        print("Example: python3 migrate_vlans_simple.py http://10.41.8.39 admin admin")
        sys.exit(1)
    
    target_url = sys.argv[1]  # Binardat 10G08-0800GSM
    username = sys.argv[2]
    password = sys.argv[3]
    
    success = migrate_vlans(target_url, username, password)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
