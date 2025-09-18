#!/usr/bin/env python3
"""
Explore 10.41.8.36 switch to find available configuration pages
"""

import requests
import hashlib
from bs4 import BeautifulSoup

def explore_switch_36():
    url = "http://10.41.8.36"
    username = "admin"
    password = "admin"
    
    # Create session
    session = requests.Session()
    session.verify = False
    
    print("1. Getting login page...")
    login_page = session.get(f"{url}/login.cgi")
    print(f"Login page status: {login_page.status_code}")
    
    # Try MD5 authentication
    print("\n2. Trying MD5 authentication...")
    md5_hash = hashlib.md5((username + password).encode()).hexdigest()
    
    auth_data = {
        'username': username,
        'password': md5_hash,
        'md5': '1'
    }
    
    response = session.post(f"{url}/login.cgi", data=auth_data, 
                          headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    print(f"Response status: {response.status_code}")
    
    if "login.cgi" not in response.text:
        print("✅ Authentication successful!")
        
        # Try to access the main page and look for links
        print("\n3. Exploring main page...")
        main_response = session.get(f"{url}/")
        print(f"Main page status: {main_response.status_code}")
        
        # Save main page for analysis
        with open('main_page_36.html', 'w') as f:
            f.write(main_response.text)
        print("Main page saved to main_page_36.html")
        
        # Look for links in the main page
        soup = BeautifulSoup(main_response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        print(f"\nFound {len(links)} links:")
        for link in links:
            href = link.get('href')
            text = link.get_text(strip=True)
            print(f"  {href} -> {text}")
        
        # Try common configuration pages
        config_pages = [
            'system.cgi',
            'config.cgi', 
            'admin.cgi',
            'vlan.cgi',
            'vlan.html',
            'port.cgi',
            'port.html',
            'mac.cgi',
            'mac.html',
            'ip.cgi',
            'ip.html',
            'user.cgi',
            'user.html',
            'status.cgi',
            'status.html',
            'info.cgi',
            'info.html'
        ]
        
        print(f"\n4. Testing configuration pages...")
        for page in config_pages:
            try:
                response = session.get(f"{url}/{page}")
                print(f"  {page}: Status {response.status_code}, Length {len(response.text)}")
                
                if response.status_code == 200 and len(response.text) > 500:
                    print(f"    ✅ {page} looks promising!")
                    # Save the page
                    with open(f'config_{page.replace(".", "_")}.html', 'w') as f:
                        f.write(response.text)
                    print(f"    Saved to config_{page.replace('.', '_')}.html")
            except Exception as e:
                print(f"    ❌ {page}: Error {e}")
        
        return True
    else:
        print("❌ Authentication failed")
        return False

if __name__ == "__main__":
    explore_switch_36()
