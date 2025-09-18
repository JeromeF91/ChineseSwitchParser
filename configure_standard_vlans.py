#!/usr/bin/env python3
"""
Standard VLAN Configuration Script for Binardat 10G08-0800GSM
This script configures standard VLANs on the switch.
"""

import sys
import json
from datetime import datetime
from modular_parser import ModularParser

# Standard VLAN configuration
STANDARD_VLANS = [
    {"id": 1, "name": "Default", "description": "Default VLAN"},
    {"id": 10, "name": "Management", "description": "Network Management"},
    {"id": 20, "name": "Servers", "description": "Server VLAN"},
    {"id": 30, "name": "Workstations", "description": "Workstation VLAN"},
    {"id": 40, "name": "WiFi", "description": "Wireless Network"},
    {"id": 50, "name": "Guests", "description": "Guest Network"},
    {"id": 100, "name": "Voice", "description": "VoIP Network"},
    {"id": 200, "name": "Security", "description": "Security Cameras"},
    {"id": 300, "name": "IoT", "description": "Internet of Things"},
    {"id": 400, "name": "DMZ", "description": "Demilitarized Zone"}
]

def configure_standard_vlans(switch_url, username, password):
    """Configure standard VLANs on the switch."""
    print("🔧 Configuring Standard VLANs on Binardat 10G08-0800GSM")
    print("=" * 60)
    
    # Initialize the parser
    parser = ModularParser()
    
    try:
        # Connect to the switch
        print(f"📡 Connecting to {switch_url}...")
        if not parser.connect(switch_url, username, password, "10G08-0800GSM"):
            print("❌ Failed to connect to switch")
            return False
        
        print("✅ Connected successfully!")
        
        # Get current VLAN configuration
        print("\n📋 Checking current VLAN configuration...")
        current_data = parser.extract_all_data()
        
        # Check if VLAN data is available
        if 'vlan_info' not in current_data or 'static_vlans' not in current_data.get('vlan_info', {}):
            print("⚠️  VLAN information not accessible. This may be due to:")
            print("   - Session management issues")
            print("   - Insufficient permissions")
            print("   - Switch configuration restrictions")
            print("\n🔧 Manual Configuration Required:")
            print("   Please configure VLANs manually through the web interface:")
            print(f"   {switch_url}")
            return False
        
        current_vlans = current_data['vlan_info']['static_vlans']
        print(f"📊 Found {len(current_vlans)} existing VLANs")
        
        # Configure each standard VLAN
        configured_vlans = []
        for vlan in STANDARD_VLANS:
            print(f"\n🔧 Configuring VLAN {vlan['id']}: {vlan['name']}")
            
            # Check if VLAN already exists
            existing_vlan = next((v for v in current_vlans if str(v.get('vlan_id', '')) == str(vlan['id'])), None)
            
            if existing_vlan:
                print(f"   ✅ VLAN {vlan['id']} already exists: {existing_vlan.get('vlan_name', 'Unknown')}")
            else:
                # Create the VLAN
                print(f"   ➕ Creating VLAN {vlan['id']}...")
                if parser.create_vlan(vlan['id'], vlan['name']):
                    print(f"   ✅ VLAN {vlan['id']} created successfully")
                    configured_vlans.append(vlan)
                else:
                    print(f"   ❌ Failed to create VLAN {vlan['id']}")
        
        # Save configuration
        print(f"\n💾 Saving configuration...")
        if parser.save_configuration():
            print("✅ Configuration saved successfully")
        else:
            print("⚠️  Configuration save not implemented or failed")
        
        # Generate summary
        print("\n📊 Configuration Summary:")
        print("=" * 40)
        print(f"Total VLANs configured: {len(configured_vlans)}")
        print(f"Existing VLANs found: {len(current_vlans)}")
        
        if configured_vlans:
            print("\nNewly configured VLANs:")
            for vlan in configured_vlans:
                print(f"  - VLAN {vlan['id']}: {vlan['name']} ({vlan['description']})")
        
        # Export final configuration
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = f"standard_vlans_config_{timestamp}.json"
        
        final_data = parser.extract_all_data()
        with open(export_file, 'w') as f:
            json.dump(final_data, f, indent=2)
        
        print(f"\n📁 Configuration exported to: {export_file}")
        print("\n✅ Standard VLAN configuration completed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during configuration: {str(e)}")
        return False
    
    finally:
        parser.disconnect()

def main():
    """Main function."""
    if len(sys.argv) != 4:
        print("Usage: python3 configure_standard_vlans.py <switch_url> <username> <password>")
        print("Example: python3 configure_standard_vlans.py http://10.41.8.39 admin admin")
        sys.exit(1)
    
    switch_url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    
    success = configure_standard_vlans(switch_url, username, password)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
