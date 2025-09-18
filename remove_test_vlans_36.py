#!/usr/bin/env python3
"""
Remove test VLANs 98 and 99 from 10.41.8.36 switch
"""

import requests
import hashlib
from bs4 import BeautifulSoup

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

def delete_vlan(session, vlan_id):
    """Delete a VLAN from the switch"""
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
    
    # Prepare form data for VLAN deletion
    form_data = {
        f'remove_{vlan_id}': 'on',  # Check the checkbox for this VLAN
        'cmd': 'vlanstatictbl'
    }
    
    response = session.post(f"{url}/vlan.cgi?page=getRmvVlanEntry", data=form_data, headers=headers)
    
    if response.status_code == 200:
        if "success" in response.text.lower() or "deleted" in response.text.lower():
            print(f"✅ VLAN {vlan_id} deleted successfully!")
            return True
        else:
            print(f"❌ VLAN {vlan_id} deletion may have failed. Response: {response.text[:200]}")
            return False
    else:
        print(f"❌ VLAN {vlan_id} deletion failed: HTTP {response.status_code}")
        return False

def list_current_vlans(session):
    """List current VLANs to verify deletion"""
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
        # Parse VLAN table
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        
        vlans = []
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    vlan_id = cells[0].get_text(strip=True)
                    vlan_name = cells[1].get_text(strip=True)
                    if vlan_id.isdigit() and vlan_id != '':
                        vlans.append({
                            'id': vlan_id,
                            'name': vlan_name
                        })
        
        return vlans
    else:
        print("❌ Could not access VLAN page for verification")
        return []

def main():
    """Main function to remove test VLANs"""
    print("🗑️  Removing test VLANs 98 and 99 from 10.41.8.36...")
    
    # Authenticate
    session = authenticate_switch_36()
    if not session:
        return
    
    # List current VLANs before deletion
    print("\n📋 Current VLANs before deletion:")
    current_vlans = list_current_vlans(session)
    for vlan in sorted(current_vlans, key=lambda x: int(x['id'])):
        print(f"  VLAN {vlan['id']:>3}: {vlan['name']}")
    
    # Delete VLANs 98 and 99
    test_vlans = [98, 99]
    deleted_count = 0
    
    print(f"\n🔨 Deleting test VLANs...")
    for vlan_id in test_vlans:
        print(f"\nDeleting VLAN {vlan_id}...")
        if delete_vlan(session, vlan_id):
            deleted_count += 1
        else:
            print(f"❌ Failed to delete VLAN {vlan_id}")
    
    # Verify deletion
    print(f"\n🔍 Verifying deletion...")
    final_vlans = list_current_vlans(session)
    
    print(f"\n📋 VLANs after deletion:")
    for vlan in sorted(final_vlans, key=lambda x: int(x['id'])):
        print(f"  VLAN {vlan['id']:>3}: {vlan['name']}")
    
    # Check if test VLANs are gone
    remaining_test_vlans = [v for v in final_vlans if int(v['id']) in test_vlans]
    if not remaining_test_vlans:
        print(f"\n✅ Successfully removed {deleted_count} test VLANs!")
        print("✅ VLANs 98 and 99 have been completely removed.")
    else:
        print(f"\n⚠️  Warning: Some test VLANs may still exist:")
        for vlan in remaining_test_vlans:
            print(f"  VLAN {vlan['id']}: {vlan['name']}")

if __name__ == "__main__":
    main()
