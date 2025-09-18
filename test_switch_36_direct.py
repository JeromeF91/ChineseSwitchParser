#!/usr/bin/env python3
"""
Test script for 10.41.8.36 switch using direct authentication approach
"""

import requests
import hashlib
from bs4 import BeautifulSoup

def test_switch_36_direct():
    url = "http://10.41.8.36"
    username = "admin"
    password = "admin"
    
    # Create session
    session = requests.Session()
    session.verify = False
    
    print("1. Getting login page...")
    login_page = session.get(f"{url}/login.cgi")
    print(f"Login page status: {login_page.status_code}")
    
    # Try different authentication methods
    auth_methods = [
        # Method 1: MD5 with username/password
        {
            'data': {'username': username, 'password': hashlib.md5((username + password).encode()).hexdigest(), 'md5': '1'},
            'headers': {'Content-Type': 'application/x-www-form-urlencoded'}
        },
        # Method 2: Direct username/password
        {
            'data': {'username': username, 'password': password},
            'headers': {'Content-Type': 'application/x-www-form-urlencoded'}
        },
        # Method 3: Different field names
        {
            'data': {'user': username, 'pass': password},
            'headers': {'Content-Type': 'application/x-www-form-urlencoded'}
        },
        # Method 4: Try with different headers
        {
            'data': {'username': username, 'password': password},
            'headers': {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': f'{url}/login.cgi',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        }
    ]
    
    for i, method in enumerate(auth_methods, 1):
        print(f"\n{i+1}. Trying authentication method {i+1}...")
        
        # Create new session for each attempt
        session = requests.Session()
        session.verify = False
        
        response = session.post(f"{url}/login.cgi", data=method['data'], headers=method['headers'])
        print(f"Response status: {response.status_code}")
        print(f"Response content (first 200 chars): {response.text[:200]}")
        
        # Check if authentication was successful
        if "login.cgi" not in response.text and "login" not in response.text.lower():
            print("✅ Authentication successful!")
            
            # Try to access info.cgi with the same session
            print(f"\n3. Testing info.cgi with method {i+1}...")
            info_headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                'Connection': 'keep-alive',
                'Referer': f'{url}/',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
            }
            
            info_response = session.get(f"{url}/info.cgi", headers=info_headers)
            print(f"Info page status: {info_response.status_code}")
            print(f"Info page length: {len(info_response.text)}")
            
            if info_response.status_code == 200 and len(info_response.text) > 500:
                print("✅ Info page accessible!")
                
                # Save the info page
                with open(f'info_page_36_method_{i+1}.html', 'w') as f:
                    f.write(info_response.text)
                print(f"Info page saved to info_page_36_method_{i+1}.html")
                
                # Now try VLAN pages
                print(f"\n4. Testing VLAN pages with method {i+1}...")
                vlan_endpoints = [
                    f"{url}/vlan.cgi?page=static",
                    f"{url}/vlan.cgi",
                    f"{url}/vlan.html"
                ]
                
                for endpoint in vlan_endpoints:
                    print(f"\nTrying: {endpoint}")
                    vlan_response = session.get(endpoint, headers=info_headers)
                    print(f"Status: {vlan_response.status_code}, Length: {len(vlan_response.text)}")
                    
                    if vlan_response.status_code == 200 and len(vlan_response.text) > 500:
                        print("✅ Found working VLAN endpoint!")
                        
                        # Save the VLAN page
                        with open(f'vlan_page_36_method_{i+1}.html', 'w') as f:
                            f.write(vlan_response.text)
                        print(f"VLAN page saved to vlan_page_36_method_{i+1}.html")
                        
                        # Parse VLAN table
                        soup = BeautifulSoup(vlan_response.text, 'html.parser')
                        tables = soup.find_all('table')
                        print(f"Found {len(tables)} tables")
                        
                        for j, table in enumerate(tables):
                            print(f"\nTable {j+1}:")
                            rows = table.find_all('tr')
                            for k, row in enumerate(rows):
                                cells = row.find_all('td')
                                if len(cells) >= 2:
                                    vlan_id = cells[0].get_text(strip=True)
                                    vlan_name = cells[1].get_text(strip=True)
                                    print(f"  Row {k+1}: VLAN {vlan_id} -> {vlan_name}")
                                    if vlan_id.isdigit():
                                        print(f"    ✅ Valid VLAN: {vlan_id}")
                        return True
                
                print("❌ No working VLAN endpoint found")
            else:
                print("❌ Info page not accessible")
        else:
            print("❌ Authentication failed")
    
    print("\n❌ All authentication methods failed")
    return False

if __name__ == "__main__":
    test_switch_36_direct()
