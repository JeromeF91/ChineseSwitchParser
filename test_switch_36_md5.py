#!/usr/bin/env python3
"""
Test script for 10.41.8.36 switch using MD5 authentication like SL-SWTG124AS
"""

import requests
import hashlib
import time
from bs4 import BeautifulSoup

def test_switch_36_md5():
    url = "http://10.41.8.36"
    username = "admin"
    password = "admin"
    
    # Create session
    session = requests.Session()
    session.verify = False
    
    print("1. Getting login page...")
    login_page = session.get(f"{url}/login.cgi")
    print(f"Login page status: {login_page.status_code}")
    
    # Try MD5 authentication like SL-SWTG124AS
    print("\n2. Trying MD5 authentication...")
    
    # Create MD5 hash of username+password
    md5_hash = hashlib.md5((username + password).encode()).hexdigest()
    print(f"MD5 hash: {md5_hash}")
    
    # Try authentication with MD5
    auth_data = {
        'username': username,
        'password': md5_hash,
        'md5': '1'
    }
    
    response = session.post(f"{url}/login.cgi", data=auth_data, 
                          headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    print(f"Response status: {response.status_code}")
    print(f"Response content (first 200 chars): {response.text[:200]}")
    
    # Check if authentication was successful
    if "login.cgi" not in response.text and "login" not in response.text.lower():
        print("✅ MD5 Authentication successful!")
        
        # Try to access main page
        print("\n3. Accessing main page...")
        main_response = session.get(f"{url}/")
        print(f"Main page status: {main_response.status_code}")
        print(f"Main page content (first 500 chars): {main_response.text[:500]}")
        
        # Try VLAN endpoints
        vlan_endpoints = [
            f"{url}/vlan.cgi?page=static",
            f"{url}/vlan.cgi",
            f"{url}/vlan.html"
        ]
        
        for endpoint in vlan_endpoints:
            print(f"\n4. Trying VLAN endpoint: {endpoint}")
            vlan_response = session.get(endpoint)
            print(f"Status: {vlan_response.status_code}, Length: {len(vlan_response.text)}")
            
            if vlan_response.status_code == 200 and len(vlan_response.text) > 500:
                print("✅ Found working VLAN endpoint!")
                
                # Save the content
                with open('vlan_page_36_md5.html', 'w') as f:
                    f.write(vlan_response.text)
                print("VLAN page saved to vlan_page_36_md5.html")
                
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
        print("❌ MD5 Authentication failed")
        return False

if __name__ == "__main__":
    test_switch_36_md5()
