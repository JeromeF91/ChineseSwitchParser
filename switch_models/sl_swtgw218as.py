"""
SL-SWTGW218AS switch model implementation.
This is the specific implementation for the SL-SWTGW218AS switch model.
"""

import requests
import hashlib
from typing import Dict, Any, List, Optional
from .base import BaseSwitchModel
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SLSWTGW218AS(BaseSwitchModel):
    """SL-SWTGW218AS switch model implementation."""
    
    def get_model_name(self) -> str:
        """Return the model name of this switch."""
        return "SL-SWTGW218AS"
    
    def get_api_endpoints(self) -> Dict[str, str]:
        """Return the API endpoints specific to this model."""
        return {
            'system_info': 'info.cgi',
            'port_status': 'port.cgi',
            'port_statistics': 'port.cgi?page=stats',
            'port_config': 'port.cgi',
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
        """Authenticate with the SL-SWTGW218AS switch."""
        try:
            # Calculate MD5 hash exactly like the JavaScript does
            md5_hash = hashlib.md5((self.username + self.password).encode()).hexdigest()
            
            # Set the admin cookie manually
            self.session.cookies.set('admin', md5_hash)
            
            # Submit the form with the Response field
            form_data = {
                'username': self.username,
                'password': self.password,
                'Response': md5_hash
            }
            
            response = self.session.post(f"{self.url}/login.cgi", data=form_data, 
                                      headers={'Content-Type': 'application/x-www-form-urlencoded'})
            
            if "login.cgi" not in response.text and "login" not in response.text.lower():
                self.console.print("[green]Authentication successful![/green]")
                return True
            else:
                self.console.print("[red]Authentication failed[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Authentication error: {str(e)}[/red]")
            return False
    
    def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """Make a request to a specific endpoint with proper headers."""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Connection': 'keep-alive',
            'Referer': f'{self.url}/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        }
        
        response = self.session.get(f"{self.url}/{endpoint}", headers=headers, timeout=10)
        
        if response.status_code == 200 and len(response.text) > 500:
            return {
                'success': True,
                'data': self._parse_html_content(response.text, endpoint),
                'raw_html': response.text
            }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}, Length: {len(response.text)}"
            }
    
    def _parse_html_content(self, html_content: str, endpoint: str) -> Dict[str, Any]:
        """Parse HTML content based on the endpoint."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        if 'info.cgi' in endpoint:
            return self._parse_system_info(soup)
        elif 'vlan.cgi' in endpoint:
            return self._parse_vlan_info(soup)
        elif 'port.cgi' in endpoint:
            return self._parse_port_info(soup)
        elif 'mac.cgi' in endpoint:
            return self._parse_mac_info(soup)
        elif 'ip.cgi' in endpoint:
            return self._parse_ip_info(soup)
        elif 'user.cgi' in endpoint:
            return self._parse_user_info(soup)
        else:
            return {'content': 'Unknown endpoint'}
    
    def _parse_system_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse system information from info.cgi."""
        info = {}
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        info[key] = value
        
        return info
    
    def _parse_vlan_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse VLAN information from vlan.cgi."""
        vlans = []
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    vlan_id = cells[0].get_text(strip=True)
                    vlan_name = cells[1].get_text(strip=True)
                    ports = cells[2].get_text(strip=True) if len(cells) > 2 else "N/A"
                    
                    if vlan_id.isdigit() and vlan_id != '':
                        vlans.append({
                            'vlan_id': vlan_id,
                            'vlan_name': vlan_name,
                            'ports': ports
                        })
        
        return {'vlans': vlans}
    
    def _parse_port_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse port information from port.cgi."""
        ports = []
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:  # Port, State, Speed, Flow Control
                    port_info = {
                        'port': cells[0].get_text(strip=True),
                        'state': cells[1].get_text(strip=True),
                        'speed': cells[2].get_text(strip=True),
                        'flow_control': cells[3].get_text(strip=True)
                    }
                    ports.append(port_info)
        
        return {'ports': ports}
    
    def _parse_mac_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse MAC address information from mac.cgi."""
        mac_entries = []
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:  # No, MAC, VLAN, Port
                    if cells[0].get_text(strip=True).isdigit():
                        mac_info = {
                            'mac_address': cells[1].get_text(strip=True),
                            'vlan': cells[2].get_text(strip=True),
                            'port': cells[3].get_text(strip=True),
                            'type': 'dynamic'
                        }
                        mac_entries.append(mac_info)
        
        return {'mac_entries': mac_entries}
    
    def _parse_ip_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse IP settings from ip.cgi."""
        ip_info = {}
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        ip_info[key] = value
        
        return ip_info
    
    def _parse_user_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse user account information from user.cgi."""
        return {'content': 'User account information'}
    
    def create_vlan(self, vlan_id: int, vlan_name: str) -> bool:
        """Create a VLAN on SL-SWTGW218AS switch."""
        try:
            if not self.authenticate():
                return False
            
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                'Connection': 'keep-alive',
                'Referer': f'{self.url}/vlan.cgi?page=static',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Prepare form data for VLAN creation
            form_data = {
                'vid': str(vlan_id),
                'name': vlan_name,
                'cmd': 'vlanstatic'
            }
            
            # Add port assignments for all 24 ports (untagged)
            for i in range(24):
                form_data[f'vlanPort_{i}'] = '0'
            
            response = self.session.post(f"{self.url}/vlan.cgi?page=static", data=form_data, headers=headers)
            
            if response.status_code == 200:
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
        """Delete a VLAN on SL-SWTGW218AS switch."""
        try:
            if not self.authenticate():
                return False
            
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                'Connection': 'keep-alive',
                'Referer': f'{self.url}/vlan.cgi?page=static',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Prepare form data for VLAN deletion
            form_data = {
                f'remove_{vlan_id}': 'on',  # Check the checkbox for this VLAN
                'cmd': 'vlanstatictbl'
            }
            
            response = self.session.post(f"{self.url}/vlan.cgi?page=getRmvVlanEntry", data=form_data, headers=headers)
            
            if response.status_code == 200:
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
    
    def enable_ssh(self) -> bool:
        """Enable SSH on SL-SWTGW218AS switch."""
        self.console.print(f"[yellow]SSH enable not implemented for {self.model_name}[/yellow]")
        return False
    
    def disable_ssh(self) -> bool:
        """Disable SSH on SL-SWTGW218AS switch."""
        self.console.print(f"[yellow]SSH disable not implemented for {self.model_name}[/yellow]")
        return False
