#!/usr/bin/env python3
"""
Test script for 10.41.8.36 switch authentication and VLAN configuration
"""

import requests
import time
from bs4 import BeautifulSoup

def test_switch_36():
    url = "http://10.41.8.36"
    username = "admin"
    password = "admin"
    
    # Create session
    session = requests.Session()
    session.verify = False
    
    # Try to get login page first
    print("1. Getting login page...")
    login_page = session.get(f"{url}/login.cgi")
    print(f"Login page status: {login_page.status_code}")
    
    # Try different authentication methods
    auth_methods = [
        # Method 1: Try with different field names (this worked before)
        {
            'url': f"{url}/login.cgi",
            'data': {'user': username, 'pass': password},
            'headers': {'Content-Type': 'application/x-www-form-urlencoded'}
        },
        # Method 2: Try with MD5 hash like SL-SWTG124AS
        {
            'url': f"{url}/login.cgi",
            'data': {'username': username, 'password': password, 'md5': '1'},
            'headers': {'Content-Type': 'application/x-www-form-urlencoded'}
        },
        # Method 3: Try with different field names
        {
            'url': f"{url}/login.cgi",
            'data': {'username': username, 'password': password},
            'headers': {'Content-Type': 'application/x-www-form-urlencoded'}
        }
    ]
    
    for i, method in enumerate(auth_methods, 1):
        print(f"\n{i+1}. Trying authentication method {i+1}...")
        try:
            if method['data']:
                response = session.post(method['url'], data=method['data'], headers=method['headers'])
            else:
                response = session.get(method['url'], headers=method['headers'])
            
            print(f"Response status: {response.status_code}")
            print(f"Response content (first 200 chars): {response.text[:200]}")
            
            # Check if we got redirected away from login
            if "login.cgi" not in response.text and "login" not in response.text.lower():
                print("✅ Authentication successful!")
                
                # Try to access main page first to establish session
                print("\n3. Accessing main page...")
                main_response = session.get(f"{url}/")
                print(f"Main page status: {main_response.status_code}")
                print(f"Main page content (first 500 chars): {main_response.text[:500]}")
                
                # Try different VLAN endpoints
                vlan_endpoints = [
                    f"{url}/vlan.cgi?page=static",
                    f"{url}/vlan.cgi",
                    f"{url}/vlan.html",
                    f"{url}/vlan",
                    f"{url}/vlan_static.cgi",
                    f"{url}/vlan_static.html"
                ]
                
                for endpoint in vlan_endpoints:
                    print(f"\n4. Trying VLAN endpoint: {endpoint}")
                    vlan_response = session.get(endpoint)
                    print(f"Status: {vlan_response.status_code}, Length: {len(vlan_response.text)}")
                    
                    if vlan_response.status_code == 200 and len(vlan_response.text) > 500:
                        print("✅ Found working VLAN endpoint!")
                        # Save the content
                        with open('vlan_page_36.html', 'w') as f:
                            f.write(vlan_response.text)
                        print("VLAN page saved to vlan_page_36.html")
                        
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
                print("❌ Still redirected to login")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n❌ All authentication methods failed")
    return False

if __name__ == "__main__":
    test_switch_36()
