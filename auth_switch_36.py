#!/usr/bin/env python3
"""
Proper authentication script for 10.41.8.36 switch following the exact JavaScript flow
"""

import requests
import hashlib
from bs4 import BeautifulSoup

def authenticate_switch_36():
    url = "http://10.41.8.36"
    username = "admin"
    password = "admin"
    
    # Create session
    session = requests.Session()
    session.verify = False
    
    print("1. Getting login page...")
    login_page = session.get(f"{url}/login.cgi")
    print(f"Login page status: {login_page.status_code}")
    
    # Calculate MD5 hash exactly like the JavaScript does
    md5_hash = hashlib.md5((username + password).encode()).hexdigest()
    print(f"MD5 hash: {md5_hash}")
    
    # Set the admin cookie manually (like the JavaScript does)
    session.cookies.set('admin', md5_hash)
    print(f"Set admin cookie: {md5_hash}")
    
    # Submit the form with the Response field (like the JavaScript does)
    print("\n2. Submitting login form...")
    form_data = {
        'username': username,
        'password': password,
        'Response': md5_hash  # This is the key field that was missing!
    }
    
    response = session.post(f"{url}/login.cgi", data=form_data, 
                          headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    print(f"Response status: {response.status_code}")
    print(f"Response content (first 200 chars): {response.text[:200]}")
    
    # Check if authentication was successful
    if "login.cgi" not in response.text and "login" not in response.text.lower():
        print("✅ Authentication successful!")
        
        # Test the info.cgi page with proper headers
        print("\n3. Testing info.cgi...")
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Connection': 'keep-alive',
            'Referer': f'{url}/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        }
        
        info_response = session.get(f"{url}/info.cgi", headers=headers)
        print(f"Info page status: {info_response.status_code}")
        print(f"Info page length: {len(info_response.text)}")
        
        if info_response.status_code == 200 and len(info_response.text) > 500:
            print("✅ Info page accessible!")
            
            # Save the info page
            with open('info_page_36_working.html', 'w') as f:
                f.write(info_response.text)
            print("Info page saved to info_page_36_working.html")
            
            # Now try VLAN pages
            print("\n4. Testing VLAN pages...")
            vlan_endpoints = [
                f"{url}/vlan.cgi?page=static",
                f"{url}/vlan.cgi",
                f"{url}/vlan.html"
            ]
            
            for endpoint in vlan_endpoints:
                print(f"\nTrying: {endpoint}")
                vlan_response = session.get(endpoint, headers=headers)
                print(f"Status: {vlan_response.status_code}, Length: {len(vlan_response.text)}")
                
                if vlan_response.status_code == 200 and len(vlan_response.text) > 500:
                    print("✅ Found working VLAN endpoint!")
                    
                    # Save the VLAN page
                    with open('vlan_page_36_working.html', 'w') as f:
                        f.write(vlan_response.text)
                    print("VLAN page saved to vlan_page_36_working.html")
                    
                    # Parse VLAN table
                    soup = BeautifulSoup(vlan_response.text, 'html.parser')
                    tables = soup.find_all('table')
                    print(f"Found {len(tables)} tables")
                    
                    for i, table in enumerate(tables):
                        print(f"\nTable {i+1}:")
                        rows = table.find_all('tr')
                        for j, row in enumerate(rows):
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                vlan_id = cells[0].get_text(strip=True)
                                vlan_name = cells[1].get_text(strip=True)
                                print(f"  Row {j+1}: VLAN {vlan_id} -> {vlan_name}")
                                if vlan_id.isdigit():
                                    print(f"    ✅ Valid VLAN: {vlan_id}")
                    return True
            
            print("❌ No working VLAN endpoint found")
            return False
        else:
            print("❌ Info page not accessible")
            return False
    else:
        print("❌ Authentication failed")
        return False

if __name__ == "__main__":
    authenticate_switch_36()
