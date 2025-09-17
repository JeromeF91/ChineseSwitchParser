"""
SL-SWTG124AS switch model implementation.
This switch uses HTML-based interface with CGI endpoints and MD5 authentication.
"""

import requests
import hashlib
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from .base import BaseSwitchModel
import logging

logger = logging.getLogger(__name__)


class SLSWTG124AS(BaseSwitchModel):
    """SL-SWTG124AS switch model implementation."""
    
    def get_model_name(self) -> str:
        """Return the model name of this switch."""
        return "SL-SWTG124AS"
    
    def get_api_endpoints(self) -> Dict[str, str]:
        """Return the API endpoints specific to this model."""
        return {
            'system_info': 'info.cgi',
            'port_status': 'port.cgi',
            'port_statistics': 'port.cgi?page=stats',
            'vlan_static': 'vlan.cgi?page=static',
            'vlan_port_based': 'vlan.cgi?page=port_based',
            'mac_forwarding_table': 'mac.cgi?page=fwd_tbl',
            'mac_static': 'mac.cgi?page=static',
            'ip_settings': 'ip.cgi',
            'user_accounts': 'user.cgi'
        }
    
    def get_login_endpoint(self) -> str:
        """Return the login endpoint for this model."""
        return "login.cgi"
    
    def authenticate(self) -> bool:
        """Authenticate with the SL-SWTG124AS switch using MD5."""
        try:
            # This switch uses MD5-based authentication via cookies
            # The authentication is done by setting a cookie with MD5(username+password)
            combined = self.username + self.password
            md5_hash = hashlib.md5(combined.encode()).hexdigest()
            
            # Set the authentication cookie
            self.session.cookies.set('admin', md5_hash)
            
            # Test authentication by accessing a protected page
            test_url = f"{self.url}/info.cgi"
            response = self.session.get(test_url, timeout=10)
            
            if response.status_code == 200 and "SL-SWTG124AS" in response.text:
                self.console.print("[green]Authentication successful![/green]")
                return True
            else:
                self.console.print("[red]Authentication failed: Invalid response[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Authentication error: {str(e)}[/red]")
            return False
    
    def get_data(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get data from a specific API endpoint and parse HTML content."""
        try:
            url = f"{self.url}/{endpoint}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # Parse HTML content
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
        if 'info.cgi' in endpoint:
            return self._parse_system_info(soup)
        elif 'port.cgi' in endpoint:
            if 'page=stats' in endpoint:
                return self._parse_port_statistics(soup)
            else:
                return self._parse_port_status(soup)
        elif 'vlan.cgi' in endpoint:
            return self._parse_vlan_info(soup)
        elif 'mac.cgi' in endpoint:
            return self._parse_mac_info(soup)
        else:
            return {"content": soup.get_text()}
    
    def _parse_system_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse system information from info.cgi."""
        info = {}
        
        # Find the system info table
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    info[key] = value
        
        return info
    
    def _parse_port_status(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse port status information from port.cgi."""
        ports = []
        
        # Find the port status table
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 6:  # Port, State, Config Speed, Actual Speed, Config Flow, Actual Flow
                    port_info = {
                        'port': cells[0].get_text(strip=True),
                        'state': cells[1].get_text(strip=True),
                        'config_speed': cells[2].get_text(strip=True),
                        'actual_speed': cells[3].get_text(strip=True),
                        'config_flow': cells[4].get_text(strip=True),
                        'actual_flow': cells[5].get_text(strip=True)
                    }
                    ports.append(port_info)
        
        return {"ports": ports}
    
    def _parse_port_statistics(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse port statistics from port.cgi?page=stats."""
        stats = []
        
        # Find the statistics table
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 8:  # Adjust based on actual table structure
                    stat_info = {
                        'port': cells[0].get_text(strip=True),
                        'state': cells[1].get_text(strip=True),
                        'link_status': cells[2].get_text(strip=True),
                        'tx_good_pkt': cells[3].get_text(strip=True),
                        'rx_good_pkt': cells[4].get_text(strip=True),
                        'tx_drop_pkt': cells[5].get_text(strip=True),
                        'rx_drop_pkt': cells[6].get_text(strip=True),
                        'collisions': cells[7].get_text(strip=True) if len(cells) > 7 else 'N/A'
                    }
                    stats.append(stat_info)
        
        return {"statistics": stats}
    
    def _parse_vlan_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse VLAN information from vlan.cgi."""
        vlans = []
        
        # Find VLAN tables
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
        """Parse MAC address information from mac.cgi."""
        mac_entries = []
        
        # Find MAC address tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 5:  # No, MAC, VLAN, Type, Port
                    # Skip header rows
                    if cells[0].get_text(strip=True).isdigit():
                        mac_info = {
                            'mac_address': cells[1].get_text(strip=True),
                            'vlan': cells[2].get_text(strip=True),
                            'port': cells[4].get_text(strip=True),
                            'type': cells[3].get_text(strip=True)
                        }
                        mac_entries.append(mac_info)
        
        return {"mac_entries": mac_entries}
    
    def extract_all_data(self) -> Dict[str, Any]:
        """Extract all available data from the SL-SWTG124AS switch."""
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
                
                self.console.print("Resolving MAC vendors (this may take a moment due to rate limiting)...")
                
                for i, mac_entry in enumerate(mac_entries, 1):
                    mac_address = mac_entry.get('mac_address', 'Unknown')
                    vlan = mac_entry.get('vlan', 'Unknown')
                    port = mac_entry.get('port', 'Unknown')
                    
                    if mac_address and mac_address != 'Unknown' and len(mac_address) > 10:
                        self.console.print(f"Looking up vendor for {mac_address} ({i}/{len(mac_entries)})...")
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
        
        # Process static MAC addresses
        if 'mac_static' in raw_data:
            mac_static = raw_data['mac_static']
            if 'data' in mac_static and 'mac_entries' in mac_static['data']:
                mac_entries = mac_static['data']['mac_entries']
                mac_info['static_macs'] = []
                
                for mac_entry in mac_entries:
                    mac_address = mac_entry.get('mac_address', 'Unknown')
                    vlan = mac_entry.get('vlan', 'Unknown')
                    port = mac_entry.get('port', 'Unknown')
                    
                    if mac_address and mac_address != 'Unknown' and len(mac_address) > 10:
                        vendor = self._resolve_mac_vendor(mac_address)
                    else:
                        vendor = "N/A"
                    
                    mac_info['static_macs'].append({
                        'mac_address': mac_address,
                        'vlan': vlan,
                        'port': port,
                        'vendor': vendor,
                        'type': mac_entry.get('type', 'Static')
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
        
        # Process port-based VLANs
        if 'vlan_port_based' in raw_data:
            vlan_port_based = raw_data['vlan_port_based']
            if 'data' in vlan_port_based and 'vlans' in vlan_port_based['data']:
                vlan_info['port_based_vlans'] = vlan_port_based['data']['vlans']
        
        return vlan_info
    
    def display_data(self, data: Dict[str, Any]) -> None:
        """Display the extracted data in a formatted way specific to SL-SWTG124AS."""
        super().display_data(data)
        
        # Display VLAN information if available
        if 'vlan_info' in data:
            self.console.print("\n[bold yellow]VLAN Information:[/bold yellow]")
            
            if 'static_vlans' in data['vlan_info']:
                self.console.print("\n[bold]Static VLANs:[/bold]")
                for vlan in data['vlan_info']['static_vlans']:
                    self.console.print(f"  VLAN {vlan['vlan_id']}: {vlan['vlan_name']} (Ports: {vlan['ports']})")
            
            if 'port_based_vlans' in data['vlan_info']:
                self.console.print("\n[bold]Port-based VLANs:[/bold]")
                for vlan in data['vlan_info']['port_based_vlans']:
                    self.console.print(f"  VLAN {vlan['vlan_id']}: {vlan['vlan_name']} (Ports: {vlan['ports']})")
        
        # Display MAC information if available
        if 'mac_info' in data:
            self.console.print("\n[bold yellow]MAC Address Information:[/bold yellow]")
            
            if 'forwarding_table' in data['mac_info']:
                self.console.print(f"\n[bold]MAC Forwarding Table ({len(data['mac_info']['forwarding_table'])} entries):[/bold]")
                for mac in data['mac_info']['forwarding_table']:
                    self.console.print(f"  {mac['mac_address']} -> {mac['vendor']} (Port: {mac['port']}, VLAN: {mac['vlan']})")
            
            if 'static_macs' in data['mac_info']:
                self.console.print(f"\n[bold]Static MAC Addresses ({len(data['mac_info']['static_macs'])} entries):[/bold]")
                for mac in data['mac_info']['static_macs']:
                    self.console.print(f"  {mac['mac_address']} -> {mac['vendor']} (Port: {mac['port']}, VLAN: {mac['vlan']})")
        
        # Display cache statistics
        with self.mac_lookup_lock:
            cache_size = len(self.mac_vendor_cache)
            self.console.print(f"\n[dim]MAC Cache: {cache_size} entries cached, current delay: {self.mac_lookup_delay}s[/dim]")
    
    def create_vlan(self, vlan_id: int, vlan_name: str) -> bool:
        """Create a VLAN on SL-SWTG124AS switch."""
        try:
            # First authenticate
            if not self.authenticate():
                return False
            
            # This switch uses HTML forms for VLAN creation
            # We need to submit a form to vlan.cgi?page=static
            vlan_url = f"{self.url}/vlan.cgi?page=static"
            
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
                'cmd': 'vlanstatic'
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': vlan_url,
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = self.session.post(vlan_url, data=form_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Check if the response indicates success
                if "success" in response.text.lower() or "vlan" in response.text.lower():
                    self.console.print(f"[green]VLAN {vlan_id} created successfully with name '{vlan_name}'![/green]")
                    return True
                else:
                    self.console.print(f"[red]VLAN creation may have failed. Response: {response.text[:200]}[/red]")
                    return False
            else:
                self.console.print(f"[red]VLAN creation failed: HTTP {response.status_code}[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error creating VLAN: {str(e)}[/red]")
            return False
    
    def delete_vlan(self, vlan_id: int) -> bool:
        """Delete a VLAN on SL-SWTG124AS switch."""
        try:
            # First authenticate
            if not self.authenticate():
                return False
            
            # This switch uses a different approach for VLAN deletion
            # We need to access the VLAN deletion form
            delete_url = f"{self.url}/vlan.cgi?page=getRmvVlanEntry"
            
            # Prepare form data for VLAN deletion
            form_data = {
                f'remove_{vlan_id}': 'on',  # Check the checkbox for this VLAN
                'cmd': 'vlanstatictbl'
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': f"{self.url}/vlan.cgi?page=static",
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = self.session.post(delete_url, data=form_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Check if the response indicates success
                if "success" in response.text.lower() or "deleted" in response.text.lower():
                    self.console.print(f"[green]VLAN {vlan_id} deleted successfully![/green]")
                    return True
                else:
                    self.console.print(f"[red]VLAN deletion may have failed. Response: {response.text[:200]}[/red]")
                    return False
            else:
                self.console.print(f"[red]VLAN deletion failed: HTTP {response.status_code}[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error deleting VLAN: {str(e)}[/red]")
            return False
