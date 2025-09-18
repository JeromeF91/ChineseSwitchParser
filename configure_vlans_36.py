#!/usr/bin/env python3
"""
Configure standard VLAN list on 10.41.8.36 switch
"""

import requests
import hashlib
from bs4 import BeautifulSoup
import time

def authenticate_switch_36():
    """Authenticate with the switch and return session"""
    url = "http://10.41.8.36"
    username = "admin"
    password = "admin"
    
    # Create session
    session = requests.Session()
    session.verify = False
    
    # Calculate MD5 hash exactly like the JavaScript does
    md5_hash = hashlib.md5((username + password).encode()).hexdigest()
    
    # Set the admin cookie manually
    session.cookies.set('admin', md5_hash)
    
    # Submit the form with the Response field
    form_data = {
        'username': username,
        'password': password,
        'Response': md5_hash
    }
    
    response = session.post(f"{url}/login.cgi", data=form_data, 
                          headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    if "login.cgi" not in response.text:
        print("✅ Authentication successful!")
        return session
    else:
        print("❌ Authentication failed")
        return None

def get_current_vlans(session):
    """Get current VLAN configuration"""
    url = "http://10.41.8.36"
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
        'Connection': 'keep-alive',
        'Referer': f'{url}/',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
    }
    
    response = session.get(f"{url}/vlan.cgi?page=static", headers=headers)
    
    if response.status_code == 200 and len(response.text) > 500:
        print("✅ VLAN page accessible!")
        
        # Parse VLAN table
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        
        current_vlans = []
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    vlan_id = cells[0].get_text(strip=True)
                    vlan_name = cells[1].get_text(strip=True)
                    if vlan_id.isdigit():
                        current_vlans.append({'id': vlan_id, 'name': vlan_name})
        
        print(f"Current VLANs: {current_vlans}")
        return current_vlans
    else:
        print("❌ Could not access VLAN page")
        return []

def create_vlan(session, vlan_id, vlan_name):
    """Create a VLAN on the switch"""
    url = "http://10.41.8.36"
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
        'Connection': 'keep-alive',
        'Referer': f'{url}/vlan.cgi?page=static',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Prepare form data for VLAN creation
    form_data = {
        'vid': str(vlan_id),
        'name': vlan_name,
        'vlanPort_0': '0',  # Port 1 - untagged
        'vlanPort_1': '0',  # Port 2 - untagged  
        'vlanPort_2': '0',  # Port 3 - untagged
        'vlanPort_3': '0',  # Port 4 - untagged
        'vlanPort_4': '0',  # Port 5 - untagged
        'vlanPort_5': '0',  # Port 6 - untagged
        'vlanPort_6': '0',  # Port 7 - untagged
        'vlanPort_7': '0',  # Port 8 - untagged
        'vlanPort_8': '0',  # Port 9 - untagged
        'vlanPort_9': '0',  # Port 10 - untagged
        'vlanPort_10': '0', # Port 11 - untagged
        'vlanPort_11': '0', # Port 12 - untagged
        'vlanPort_12': '0', # Port 13 - untagged
        'vlanPort_13': '0', # Port 14 - untagged
        'vlanPort_14': '0', # Port 15 - untagged
        'vlanPort_15': '0', # Port 16 - untagged
        'vlanPort_16': '0', # Port 17 - untagged
        'vlanPort_17': '0', # Port 18 - untagged
        'vlanPort_18': '0', # Port 19 - untagged
        'vlanPort_19': '0', # Port 20 - untagged
        'vlanPort_20': '0', # Port 21 - untagged
        'vlanPort_21': '0', # Port 22 - untagged
        'vlanPort_22': '0', # Port 23 - untagged
        'vlanPort_23': '0', # Port 24 - untagged
        'cmd': 'vlanstatic'
    }
    
    response = session.post(f"{url}/vlan.cgi?page=static", data=form_data, headers=headers)
    
    if response.status_code == 200:
        if "success" in response.text.lower() or "vlan" in response.text.lower():
            print(f"✅ VLAN {vlan_id} ({vlan_name}) created successfully!")
            return True
        else:
            print(f"❌ VLAN {vlan_id} creation may have failed. Response: {response.text[:200]}")
            return False
    else:
        print(f"❌ VLAN {vlan_id} creation failed: HTTP {response.status_code}")
        return False

def main():
    """Main function to configure standard VLAN list"""
    print("🔧 Configuring standard VLAN list on 10.41.8.36...")
    
    # Standard VLAN list
    standard_vlans = [
        {'id': 98, 'name': 'reserved'},
        {'id': 99, 'name': 'testIAC'},
        {'id': 105, 'name': 'TOR01-WAN1'},
        {'id': 106, 'name': 'TOR01-WAN2'},
        {'id': 110, 'name': 'TOR01-Management'},
        {'id': 120, 'name': 'TOR01-NetworkManagement'},
        {'id': 130, 'name': 'TOR01-Storage'},
        {'id': 140, 'name': 'TOR01-Workstations'},
        {'id': 150, 'name': 'TOR01-Servers'},
        {'id': 160, 'name': 'TOR01-ServersDMZ'},
        {'id': 170, 'name': 'TOR01-CCTV'},
        {'id': 180, 'name': 'TOR01-IOT'},
        {'id': 190, 'name': 'TOR01-GuestWifi'}
    ]
    
    # Authenticate
    session = authenticate_switch_36()
    if not session:
        return
    
    # Get current VLANs
    print("\n📋 Getting current VLAN configuration...")
    current_vlans = get_current_vlans(session)
    
    # Create missing VLANs
    print("\n🔧 Creating missing VLANs...")
    created_count = 0
    
    for vlan in standard_vlans:
        vlan_id = vlan['id']
        vlan_name = vlan['name']
        
        # Check if VLAN already exists
        if any(v['id'] == str(vlan_id) for v in current_vlans):
            print(f"⏭️  VLAN {vlan_id} ({vlan_name}) already exists, skipping...")
            continue
        
        print(f"🔨 Creating VLAN {vlan_id} ({vlan_name})...")
        if create_vlan(session, vlan_id, vlan_name):
            created_count += 1
            time.sleep(1)  # Small delay between VLAN creations
        else:
            print(f"❌ Failed to create VLAN {vlan_id}")
    
    print(f"\n✅ VLAN configuration completed! Created {created_count} new VLANs.")
    
    # Verify final configuration
    print("\n🔍 Verifying final VLAN configuration...")
    final_vlans = get_current_vlans(session)
    print(f"Final VLAN count: {len(final_vlans)}")
    for vlan in final_vlans:
        print(f"  VLAN {vlan['id']}: {vlan['name']}")

if __name__ == "__main__":
    main()
