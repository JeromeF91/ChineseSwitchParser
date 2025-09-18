#!/usr/bin/env python3
"""
List all VLANs currently configured on 10.41.8.36 switch
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

def list_vlans(session):
    """List all VLANs configured on the switch"""
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
        
        # Save the VLAN page for analysis
        with open('current_vlans_36.html', 'w') as f:
            f.write(response.text)
        print("VLAN page saved to current_vlans_36.html")
        
        # Parse VLAN table
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        
        print(f"\n📋 Found {len(tables)} tables in VLAN configuration page")
        
        vlans = []
        for i, table in enumerate(tables):
            print(f"\n🔍 Analyzing Table {i+1}:")
            rows = table.find_all('tr')
            print(f"  Rows: {len(rows)}")
            
            for j, row in enumerate(rows):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    vlan_id = cells[0].get_text(strip=True)
                    vlan_name = cells[1].get_text(strip=True)
                    ports = cells[2].get_text(strip=True) if len(cells) > 2 else "N/A"
                    
                    print(f"    Row {j+1}: VLAN {vlan_id} -> {vlan_name} (Ports: {ports})")
                    
                    if vlan_id.isdigit() and vlan_id != '':
                        vlans.append({
                            'id': vlan_id,
                            'name': vlan_name,
                            'ports': ports
                        })
                        print(f"      ✅ Valid VLAN: {vlan_id}")
        
        # Display summary
        print(f"\n📊 VLAN Summary:")
        print(f"Total VLANs found: {len(vlans)}")
        
        if vlans:
            print(f"\n📝 Configured VLANs:")
            for vlan in sorted(vlans, key=lambda x: int(x['id'])):
                print(f"  VLAN {vlan['id']:>3}: {vlan['name']:<20} (Ports: {vlan['ports']})")
        else:
            print("  No VLANs found")
        
        return vlans
    else:
        print("❌ Could not access VLAN page")
        return []

def main():
    """Main function to list VLANs"""
    print("🔍 Listing VLANs on 10.41.8.36...")
    
    # Authenticate
    session = authenticate_switch_36()
    if not session:
        return
    
    # List VLANs
    vlans = list_vlans(session)
    
    print(f"\n✅ VLAN listing completed! Found {len(vlans)} VLANs.")

if __name__ == "__main__":
    main()
