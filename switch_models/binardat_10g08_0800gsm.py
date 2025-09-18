"""
Binardat 10G08-0800GSM Layer 3 Switch model implementation.
This switch uses a modern web interface with JSON-based API endpoints and RC4 encryption.
"""

import requests
import json
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from .base import BaseSwitchModel
import logging

logger = logging.getLogger(__name__)


class Binardat10G080800GSM(BaseSwitchModel):
    """Binardat 10G08-0800GSM Layer 3 Switch model implementation."""
    
    def get_model_name(self) -> str:
        """Return the model name of this switch."""
        return "10G08-0800GSM"
    
    def get_manufacturer(self) -> str:
        """Return the manufacturer of this switch."""
        return "Binardat"
    
    def get_api_endpoints(self) -> Dict[str, str]:
        """Return the API endpoints specific to this model."""
        return {
            'login': 'login.cgi',
            'system_info': 'homepage.cgi',  # This provides device info and port status
            'port_status': 'homepage.cgi',  # Port status is included in homepage
            'port_statistics': 'port.cgi?page=stats',
            'port_config': 'port.cgi?page=config',
            'vlan_static': 'getVlanConfig.cgi?page=inside',  # Correct endpoint for VLAN listing
            'vlan_port_based': 'vlan.cgi?page=port_based',
            'mac_forwarding_table': 'mac.cgi?page=fwd_tbl',
            'mac_static': 'mac.cgi?page=static',
            'arp_table': 'getSearchMac.cgi?page=inside',
            'ip_settings': 'ip.cgi',
            'user_accounts': 'user.cgi',
            'status': 'status.cgi',
            'info': 'info.cgi'
        }
    
    def get_login_endpoint(self) -> str:
        """Return the login endpoint for this model."""
        return "login.cgi"
    
    def _rc4_encrypt(self, key: str, text: str) -> str:
        """RC4 encryption implementation matching the JavaScript version exactly."""
        S = []
        j = 0
        i = 0
        t = 0
        textLength = len(text)
        result = ''
        keyLength = len(key)
        keyIndex = 0
        
        # Initialize S-box
        for i in range(256):
            S.append(i)
        
        # Key scheduling
        j = 0
        i = 0
        for i in range(256):
            j = (j + S[i] + ord(key[keyIndex])) % 256
            # XOR swap
            S[i] = S[i] ^ S[j]
            S[j] = S[i] ^ S[j]
            S[i] = S[i] ^ S[j]
            keyIndex = (keyIndex + 1) % keyLength
        
        # Pseudo-random generation and encryption
        j = 0
        i = 0
        for y in range(textLength):
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            # XOR swap
            S[i] = S[i] ^ S[j]
            S[j] = S[i] ^ S[j]
            S[i] = S[i] ^ S[j]
            t = (S[i] + (S[j] % 256)) % 256
            result += str(ord(text[y]) ^ S[t])
            result += ',,'
        
        return result
    
    def authenticate(self) -> bool:
        """Authenticate with the Binardat 10G08-0800GSM switch using RC4 encryption."""
        try:
            import base64
            
            # This switch uses RC4 encryption for authentication
            # First, try to get a session by accessing the login page
            login_url = f"{self.url}/index.cgi"
            
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                'Connection': 'keep-alive',
                'Referer': f'{self.url}/index.cgi',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
            }
            
            # Get initial session
            response = self.session.get(login_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Now try to authenticate using the login.cgi endpoint
                auth_url = f"{self.url}/login.cgi"
                
                # Encode credentials in Base64 for cookies
                username_b64 = base64.b64encode(self.username.encode()).decode()
                password_b64 = base64.b64encode(self.password.encode()).decode()
                
                # Encrypt credentials using RC4
                rc4_key = "iensuegdul27c90d"
                encrypted_username = self._rc4_encrypt(rc4_key, self.username)
                encrypted_password = self._rc4_encrypt(rc4_key, self.password)
                
                # Prepare login data with RC4 encrypted credentials
                login_data = f'name={encrypted_username}&pwd={encrypted_password}'
                
                auth_headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': f'{self.url}/index.cgi'
                }
                
                response = self.session.post(auth_url, data=login_data, headers=auth_headers, timeout=10)
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        if result.get('code') == 0:
                            # Set the authentication cookies
                            self.session.cookies.set('webusername', username_b64)
                            self.session.cookies.set('webpassword', password_b64)
                            self.session.cookies.set('menudatalink', 'homepage.cgi')
                            
                            # Try to access the main interface to establish session
                            main_url = f"{self.url}/index.cgi"
                            main_response = self.session.get(main_url, timeout=10)
                            
                            if main_response.status_code == 200 and "User Login" not in main_response.text:
                                self.console.print("[green]Authentication successful![/green]")
                                return True
                            else:
                                self.console.print("[yellow]Authentication successful but session not established[/yellow]")
                                return True
                        elif result.get('code') == 6:
                            self.console.print("[red]Authentication failed: Insufficient permissions[/red]")
                            return False
                        else:
                            self.console.print("[red]Authentication failed: Invalid credentials[/red]")
                            return False
                    except json.JSONDecodeError:
                        self.console.print("[red]Authentication failed: Invalid response format[/red]")
                        return False
                else:
                    self.console.print(f"[red]Authentication failed: HTTP {response.status_code}[/red]")
                    return False
            else:
                self.console.print(f"[red]Failed to access login page: HTTP {response.status_code}[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Authentication error: {str(e)}[/red]")
            return False
    
    def get_data(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get data from a specific API endpoint."""
        try:
            url = f"{self.url}/{endpoint}"
            
            # Use proper headers for authenticated requests
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                'Connection': 'keep-alive',
                'Referer': f'{self.url}/index.cgi',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
            }
            
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Check if response is JSON
                try:
                    json_data = response.json()
                    return {"data": json_data, "raw_json": response.text}
                except json.JSONDecodeError:
                    # If not JSON, parse as HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    parsed_data = self._parse_html_content(soup, endpoint)
                    return {"data": parsed_data, "raw_html": response.text}
            else:
                logger.warning(f"Failed to get data from {endpoint}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting data from {endpoint}: {str(e)}")
            return None
    
    def _parse_html_content(self, soup: BeautifulSoup, endpoint: str) -> Dict[str, Any]:
        """Parse HTML content based on the endpoint type."""
        if 'homepage' in endpoint:
            return self._parse_homepage_data(soup)
        elif 'system' in endpoint or 'info' in endpoint:
            return self._parse_system_info(soup)
        elif 'port' in endpoint:
            if 'stats' in endpoint:
                return self._parse_port_statistics(soup)
            elif 'config' in endpoint:
                return self._parse_port_config(soup)
            else:
                return self._parse_port_status(soup)
        elif 'vlan' in endpoint or 'getVlanConfig' in endpoint:
            return self._parse_vlan_config(soup)
        elif 'mac' in endpoint:
            return self._parse_mac_info(soup)
        elif 'arp' in endpoint or 'getSearchMac' in endpoint:
            return self._parse_arp_table(soup)
        else:
            return {"content": soup.get_text()}
    
    def _parse_system_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse system information."""
        info = {}
        
        # Look for system info in various formats
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    info[key] = value
        
        # Look for system info in divs or other elements
        info_divs = soup.find_all(['div', 'span'], class_=lambda x: x and any(word in x.lower() for word in ['info', 'system', 'device', 'model']))
        for div in info_divs:
            text = div.get_text(strip=True)
            if ':' in text:
                parts = text.split(':', 1)
                if len(parts) == 2:
                    info[parts[0].strip()] = parts[1].strip()
        
        return info
    
    def _parse_port_status(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse port status information."""
        ports = []
        
        # Look for port status tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:  # Minimum columns for port info
                    port_info = {
                        'port': cells[0].get_text(strip=True),
                        'status': cells[1].get_text(strip=True) if len(cells) > 1 else 'Unknown',
                        'speed': cells[2].get_text(strip=True) if len(cells) > 2 else 'Unknown',
                        'duplex': cells[3].get_text(strip=True) if len(cells) > 3 else 'Unknown'
                    }
                    ports.append(port_info)
        
        return {"ports": ports}
    
    def _parse_port_statistics(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse port statistics."""
        stats = []
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:  # Minimum columns for stats
                    stat_info = {
                        'port': cells[0].get_text(strip=True),
                        'tx_packets': cells[1].get_text(strip=True) if len(cells) > 1 else '0',
                        'rx_packets': cells[2].get_text(strip=True) if len(cells) > 2 else '0',
                        'tx_bytes': cells[3].get_text(strip=True) if len(cells) > 3 else '0',
                        'rx_bytes': cells[4].get_text(strip=True) if len(cells) > 4 else '0'
                    }
                    stats.append(stat_info)
        
        return {"statistics": stats}
    
    def _parse_port_config(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse port configuration."""
        ports = []
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    port_info = {
                        'port': cells[0].get_text(strip=True),
                        'enabled': 'enable' in cells[1].get_text(strip=True).lower() if len(cells) > 1 else False,
                        'speed': cells[2].get_text(strip=True) if len(cells) > 2 else 'Unknown',
                        'duplex': cells[3].get_text(strip=True) if len(cells) > 3 else 'Unknown'
                    }
                    ports.append(port_info)
        
        return {"ports": ports}
    
    def _parse_vlan_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse VLAN information."""
        vlans = []
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    vlan_info = {
                        'vlan_id': cells[0].get_text(strip=True),
                        'vlan_name': cells[1].get_text(strip=True) if len(cells) > 1 else 'N/A',
                        'ports': cells[2].get_text(strip=True) if len(cells) > 2 else 'N/A'
                    }
                    vlans.append(vlan_info)
        
        return {"vlans": vlans}
    
    def _parse_mac_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse MAC address information."""
        mac_entries = []
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    mac_info = {
                        'mac_address': cells[0].get_text(strip=True),
                        'vlan': cells[1].get_text(strip=True) if len(cells) > 1 else 'Unknown',
                        'port': cells[2].get_text(strip=True) if len(cells) > 2 else 'Unknown',
                        'type': cells[3].get_text(strip=True) if len(cells) > 3 else 'Unknown'
                    }
                    mac_entries.append(mac_info)
        
        return {"mac_entries": mac_entries}
    
    def _parse_vlan_config(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse VLAN configuration from getVlanConfig.cgi."""
        vlans = []
        
        # Find VLAN tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:  # VLAN ID, Name, Ports
                    # Skip header rows and empty rows
                    vlan_id_text = cells[0].get_text(strip=True)
                    if vlan_id_text.isdigit():
                        vlan_info = {
                            'id': int(vlan_id_text),
                            'name': cells[1].get_text(strip=True),
                            'ports': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                            'untagged': cells[3].get_text(strip=True) if len(cells) > 3 else '',
                            'tagged': cells[4].get_text(strip=True) if len(cells) > 4 else ''
                        }
                        vlans.append(vlan_info)
        
        return {"vlans": vlans}
    
    def _parse_arp_table(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse ARP table information from getSearchMac.cgi."""
        arp_entries = []
        
        # Find MAC address tables (same structure as ARP table)
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 5:  # VLAN, MAC, Type, Creator, Port
                    # Skip header rows
                    if cells[0].get_text(strip=True).isdigit():
                        arp_info = {
                            'vlan_id': cells[0].get_text(strip=True),
                            'mac_address': cells[1].get_text(strip=True),
                            'type': cells[2].get_text(strip=True),
                            'creator': cells[3].get_text(strip=True),
                            'port': cells[4].get_text(strip=True)
                        }
                        arp_entries.append(arp_info)
        
        return {"arp_entries": arp_entries}
    
    def _parse_homepage_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse system info and port status from homepage.cgi."""
        data = {
            'device_info': {},
            'ports': []
        }
        
        # Parse device information table
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    # Check if this is a device info row
                    if any('Hostname' in cell.get_text() or 'IP Address' in cell.get_text() or 'Uptime' in cell.get_text() for cell in cells):
                        for i in range(0, len(cells), 2):
                            if i + 1 < len(cells):
                                key = cells[i].get_text(strip=True).replace(':', '').replace('<b>', '').replace('</b>', '')
                                value = cells[i + 1].get_text(strip=True)
                                if key and value:
                                    data['device_info'][key] = value
                    # Check if this is a port status row
                    elif any('Ethernet' in cell.get_text() for cell in cells):
                        if len(cells) >= 6:
                            port_info = {
                                'port': cells[0].get_text(strip=True),
                                'status': cells[1].get_text(strip=True),
                                'type': cells[2].get_text(strip=True),
                                'speed': cells[3].get_text(strip=True),
                                'duplex': cells[4].get_text(strip=True),
                                'auto_negotiation': cells[5].get_text(strip=True) if len(cells) > 5 else ''
                            }
                            data['ports'].append(port_info)
        
        return data
    
    def extract_all_data(self) -> Dict[str, Any]:
        """Extract all available data from the Binardat 10G08-0800GSM switch."""
        data = super().extract_all_data()
        
        # Add model-specific data processing
        if 'mac_forwarding_table' in data.get('data', {}):
            data['mac_info'] = self._process_mac_data(data['data'])
        
        if 'vlan_static' in data.get('data', {}):
            data['vlan_info'] = self._process_vlan_data(data['data'])
        
        return data
    
    def _process_mac_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process MAC address data for better display."""
        mac_info = {}
        
        # Process MAC forwarding table
        if 'mac_forwarding_table' in raw_data:
            mac_forwarding = raw_data['mac_forwarding_table']
            if 'data' in mac_forwarding and 'mac_entries' in mac_forwarding['data']:
                mac_entries = mac_forwarding['data']['mac_entries']
                mac_info['forwarding_table'] = []
                
                for mac_entry in mac_entries:
                    mac_address = mac_entry.get('mac_address', 'Unknown')
                    vlan = mac_entry.get('vlan', 'Unknown')
                    port = mac_entry.get('port', 'Unknown')
                    
                    if mac_address and mac_address != 'Unknown' and len(mac_address) > 10:
                        vendor = self._resolve_mac_vendor(mac_address)
                    else:
                        vendor = "N/A"
                    
                    mac_info['forwarding_table'].append({
                        'mac_address': mac_address,
                        'vlan': vlan,
                        'port': port,
                        'vendor': vendor,
                        'type': mac_entry.get('type', 'N/A')
                    })
        
        return mac_info
    
    def _process_vlan_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process VLAN data for better display."""
        vlan_info = {}
        
        # Process static VLANs
        if 'vlan_static' in raw_data:
            vlan_static = raw_data['vlan_static']
            if 'data' in vlan_static and 'vlans' in vlan_static['data']:
                vlan_info['static_vlans'] = vlan_static['data']['vlans']
        
        return vlan_info
    
    def display_data(self, data: Dict[str, Any]) -> None:
        """Display the extracted data in a formatted way specific to Binardat 10G08-0800GSM."""
        super().display_data(data)
        
        # Display VLAN information if available
        if 'vlan_info' in data:
            self.console.print("\n[bold yellow]VLAN Information:[/bold yellow]")
            
            if 'static_vlans' in data['vlan_info']:
                self.console.print("\n[bold]Static VLANs:[/bold]")
                for vlan in data['vlan_info']['static_vlans']:
                    self.console.print(f"  VLAN {vlan['vlan_id']}: {vlan['vlan_name']} (Ports: {vlan['ports']})")
        
        # Display MAC information if available
        if 'mac_info' in data:
            self.console.print("\n[bold yellow]MAC Address Information:[/bold yellow]")
            
            if 'forwarding_table' in data['mac_info']:
                self.console.print(f"\n[bold]MAC Forwarding Table ({len(data['mac_info']['forwarding_table'])} entries):[/bold]")
                for mac in data['mac_info']['forwarding_table']:
                    self.console.print(f"  {mac['mac_address']} -> {mac['vendor']} (Port: {mac['port']}, VLAN: {mac['vlan']})")
    
    def create_vlan(self, vlan_id: int, vlan_name: str) -> bool:
        """Create a VLAN on Binardat 10G08-0800GSM switch using setVlanConfig.cgi endpoint."""
        try:
            if not self.authenticate():
                return False
            
            # Prepare the data for VLAN creation
            data = {
                'vid': str(vlan_id),
                'name': vlan_name,
                'cmd': 'add',
                'page': 'inside'
            }
            
            # Make the request to create VLAN
            response = self.session.post(
                f"{self.url}/setVlanConfig.cgi",
                data=data,
                headers={
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                    'Connection': 'keep-alive',
                    'Content-type': 'application/x-www-form-urlencoded',
                    'Origin': self.url,
                    'Referer': f"{self.url}/index.cgi",
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self.console.print(f"[green]VLAN {vlan_id} ({vlan_name}) created successfully.[/green]")
                return True
            else:
                self.console.print(f"[red]Failed to create VLAN {vlan_id}: HTTP {response.status_code}[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error creating VLAN {vlan_id}: {str(e)}[/red]")
            return False
    
    def delete_vlan(self, vlan_id: int) -> bool:
        """Delete a VLAN on Binardat 10G08-0800GSM switch using setVlanConfig.cgi endpoint."""
        try:
            if not self.authenticate():
                return False
            
            # Prepare the data for VLAN deletion using the correct format
            # Format: del_2=99&cmd=del&maxnum=13&page=inside
            data = {
                f'del_2': str(vlan_id),  # Use del_2 format as shown in curl
                'cmd': 'del',
                'maxnum': '13',  # Include maxnum parameter
                'page': 'inside'
            }
            
            # Make the request to delete VLAN
            response = self.session.post(
                f"{self.url}/setVlanConfig.cgi",
                data=data,
                headers={
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                    'Connection': 'keep-alive',
                    'Content-type': 'application/x-www-form-urlencoded',
                    'Origin': self.url,
                    'Referer': f"{self.url}/index.cgi",
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self.console.print(f"[green]VLAN {vlan_id} deleted successfully.[/green]")
                return True
            else:
                self.console.print(f"[red]Failed to delete VLAN {vlan_id}: HTTP {response.status_code}[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error deleting VLAN {vlan_id}: {str(e)}[/red]")
            return False
    
    def enable_ssh(self) -> bool:
        """Enable SSH on Binardat 10G08-0800GSM switch."""
        try:
            if not self.authenticate():
                return False
            
            # This is a placeholder - actual implementation would depend on the specific switch API
            self.console.print(f"[yellow]SSH enable not yet implemented for this switch model[/yellow]")
            return False
            
        except Exception as e:
            self.console.print(f"[red]Error enabling SSH: {str(e)}[/red]")
            return False
    
    def disable_ssh(self) -> bool:
        """Disable SSH on Binardat 10G08-0800GSM switch."""
        try:
            if not self.authenticate():
                return False
            
            # This is a placeholder - actual implementation would depend on the specific switch API
            self.console.print(f"[yellow]SSH disable not yet implemented for this switch model[/yellow]")
            return False
            
        except Exception as e:
            self.console.print(f"[red]Error disabling SSH: {str(e)}[/red]")
            return False
    
    def save_configuration(self) -> bool:
        """Save configuration to flash memory on Binardat 10G08-0800GSM switch."""
        try:
            if not self.authenticate():
                return False
            
            # Use the correct save endpoint for Binardat switches
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                'Connection': 'keep-alive',
                'Content-type': 'application/x-www-form-urlencoded',
                'Origin': self.url,
                'Referer': f'{self.url}/index.cgi',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
            }
            
            # Send POST request to syscmd.cgi with save command
            data = 'cmd=save&page=inside'
            response = self.session.post(
                f"{self.url}/syscmd.cgi",
                headers=headers,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.console.print("[green]Configuration saved successfully using syscmd.cgi[/green]")
                return True
            else:
                self.console.print(f"[yellow]Failed to save configuration: HTTP {response.status_code}[/yellow]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error saving configuration: {str(e)}[/red]")
            return False
