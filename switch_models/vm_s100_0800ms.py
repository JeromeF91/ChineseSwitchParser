"""
VM-S100-0800MS switch model implementation.
This is the specific implementation for the VM-S100-0800MS switch model.
"""

import requests
import time
from typing import Dict, Any
from .base import BaseSwitchModel
import logging

logger = logging.getLogger(__name__)


class VMS1000800MS(BaseSwitchModel):
    """VM-S100-0800MS switch model implementation."""
    
    def get_model_name(self) -> str:
        """Return the model name of this switch."""
        return "VM-S100-0800MS"
    
    def get_api_endpoints(self) -> Dict[str, str]:
        """Return the API endpoints specific to this model."""
        return {
            'system_info': 'cgi/get.cgi?cmd=sys_sysinfo',
            'cpu_memory': 'cgi/get.cgi?cmd=sys_cpumem',
            'port_count': 'cgi/get.cgi?cmd=port_cnt',
            'port_bandwidth': 'cgi/get.cgi?cmd=port_bwutilz',
            'lag_info': 'cgi/get.cgi?cmd=lag_mgmt',
            'syslog': 'cgi/get.cgi?cmd=log_syslog',
            'panel_info': 'cgi/get.cgi?cmd=panel_info',
            'panel_layout': 'cgi/get.cgi?cmd=panel_layout',
            'vlan_config': 'cgi/get.cgi?cmd=vlan_conf',
            'vlan_membership': 'cgi/get.cgi?cmd=vlan_membership',
            'vlan_port': 'cgi/get.cgi?cmd=vlan_port',
            'mac_dynamic': 'cgi/get.cgi?cmd=mac_dynamic',
            'mac_static': 'cgi/get.cgi?cmd=mac_static',
            'mac_status': 'cgi/get.cgi?cmd=mac_miscStatus'
        }
    
    def get_login_endpoint(self) -> str:
        """Return the login endpoint for this model."""
        return "cgi/set.cgi?cmd=home_loginAuth"
    
    def authenticate(self) -> bool:
        """Authenticate with the VM-S100-0800MS switch."""
        try:
            # Prepare login data
            login_data = {
                'username': self.username,
                'password': self.password
            }
            
            # Make login request
            login_url = f"{self.url}/{self.login_endpoint}"
            response = self.session.post(login_url, data=login_data, timeout=10)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('success') or 'logout' not in result:
                        self.console.print("[green]Authentication successful![/green]")
                        return True
                    else:
                        self.console.print(f"[red]Authentication failed: {result.get('reason', 'Unknown error')}[/red]")
                        return False
                except ValueError:
                    # If not JSON, check if response contains success indicators
                    if "success" in response.text.lower() or "login" in response.text.lower():
                        self.console.print("[green]Authentication successful![/green]")
                        return True
                    else:
                        self.console.print("[red]Authentication failed: Invalid response format[/red]")
                        return False
            else:
                self.console.print(f"[red]Authentication failed: HTTP {response.status_code}[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Authentication error: {str(e)}[/red]")
            return False
    
    def extract_all_data(self) -> Dict[str, Any]:
        """Extract all available data from the VM-S100-0800MS switch."""
        data = super().extract_all_data()
        
        # Add model-specific data processing
        if 'vlan_config' in data.get('data', {}):
            data['vlan_info'] = self._process_vlan_data(data['data'])
        
        if 'mac_dynamic' in data.get('data', {}):
            data['mac_info'] = self._process_mac_data(data['data'])
        
        return data
    
    def _process_vlan_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process VLAN data for better display."""
        vlan_info = {}
        
        # Process VLAN configuration
        if 'vlan_config' in raw_data:
            vlan_config = raw_data['vlan_config']
            if 'data' in vlan_config and 'vlanList' in vlan_config['data']:
                vlan_list = vlan_config['data']['vlanList']
                vlan_info['vlan_config'] = []
                for vlan_id, vlan_name in vlan_list.items():
                    vlan_info['vlan_config'].append({
                        'vlan_id': vlan_id,
                        'vlan_name': vlan_name
                    })
        
        # Process VLAN port assignments
        if 'vlan_port' in raw_data:
            vlan_port = raw_data['vlan_port']
            if 'data' in vlan_port and 'portVlanList' in vlan_port['data']:
                port_list = vlan_port['data']['portVlanList']
                vlan_info['port_assignments'] = []
                for port, config in port_list.items():
                    vlan_info['port_assignments'].append({
                        'port': port,
                        'mode': config.get('mode'),
                        'membership': config.get('membership'),
                        'forbidden': config.get('forbidden'),
                        'pvid': config.get('pvid')
                    })
        
        return vlan_info
    
    def _process_mac_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process MAC address data for better display."""
        mac_info = {}
        
        # Process dynamic MAC addresses
        if 'mac_dynamic' in raw_data:
            mac_dynamic = raw_data['mac_dynamic']
            if 'data' in mac_dynamic and 'macList' in mac_dynamic['data']:
                mac_list = mac_dynamic['data']['macList']
                mac_info['dynamic_macs'] = []
                
                self.console.print("Resolving MAC vendors (this may take a moment due to rate limiting)...")
                
                for i, (mac_key, mac_data) in enumerate(mac_list.items(), 1):
                    mac_address = mac_data.get('mac', 'Unknown')
                    vlan = mac_data.get('vlan', 'Unknown')
                    port = mac_data.get('port', 'Unknown')
                    
                    self.console.print(f"Looking up vendor for {mac_address} ({i}/{len(mac_list)})...")
                    vendor = self._resolve_mac_vendor(mac_address)
                    
                    mac_info['dynamic_macs'].append({
                        'mac_address': mac_address,
                        'vlan': vlan,
                        'port': port,
                        'vendor': vendor,
                        'key': mac_key
                    })
        
        # Process static MAC addresses
        if 'mac_static' in raw_data:
            mac_static = raw_data['mac_static']
            if 'data' in mac_static and 'macList' in mac_static['data']:
                mac_list = mac_static['data']['macList']
                mac_info['static_macs'] = []
                
                for mac_key, mac_data in mac_list.items():
                    mac_address = mac_data.get('mac', 'Unknown')
                    vlan = mac_data.get('vlan', 'Unknown')
                    port = mac_data.get('port', 'Unknown')
                    
                    vendor = self._resolve_mac_vendor(mac_address)
                    
                    mac_info['static_macs'].append({
                        'mac_address': mac_address,
                        'vlan': vlan,
                        'port': port,
                        'vendor': vendor,
                        'key': mac_key
                    })
        
        return mac_info
    
    def display_data(self, data: Dict[str, Any]) -> None:
        """Display the extracted data in a formatted way specific to VM-S100-0800MS."""
        super().display_data(data)
        
        # Display VLAN information if available
        if 'vlan_info' in data:
            self.console.print("\n[bold yellow]VLAN Information:[/bold yellow]")
            
            if 'vlan_config' in data['vlan_info']:
                self.console.print("\n[bold]VLAN Configuration:[/bold]")
                for vlan in data['vlan_info']['vlan_config']:
                    self.console.print(f"  VLAN {vlan['vlan_id']}: {vlan['vlan_name']}")
            
            if 'port_assignments' in data['vlan_info']:
                self.console.print("\n[bold]Port VLAN Assignments:[/bold]")
                for port in data['vlan_info']['port_assignments']:
                    self.console.print(f"  {port['port']}: Mode={port['mode']}, Membership={port['membership']}")
        
        # Display MAC information if available
        if 'mac_info' in data:
            self.console.print("\n[bold yellow]MAC Address Information:[/bold yellow]")
            
            if 'dynamic_macs' in data['mac_info']:
                self.console.print(f"\n[bold]Dynamic MAC Addresses ({len(data['mac_info']['dynamic_macs'])}):[/bold]")
                for mac in data['mac_info']['dynamic_macs']:
                    self.console.print(f"  {mac['mac_address']} -> {mac['vendor']} (Port: {mac['port']}, VLAN: {mac['vlan']})")
            
            if 'static_macs' in data['mac_info']:
                self.console.print(f"\n[bold]Static MAC Addresses ({len(data['mac_info']['static_macs'])}):[/bold]")
                for mac in data['mac_info']['static_macs']:
                    self.console.print(f"  {mac['mac_address']} -> {mac['vendor']} (Port: {mac['port']}, VLAN: {mac['vlan']})")
        
        # Display cache statistics
        with self.mac_lookup_lock:
            cache_size = len(self.mac_vendor_cache)
            self.console.print(f"\n[dim]MAC Cache: {cache_size} entries cached, current delay: {self.mac_lookup_delay}s[/dim]")
    
    def create_vlan(self, vlan_id: int, vlan_name: str) -> bool:
        """Create a VLAN on VM-S100-0800MS switch."""
        try:
            # First authenticate
            if not self.authenticate():
                return False
            
            # Create VLAN using the set.cgi endpoint
            create_url = f"{self.url}/cgi/set.cgi?cmd=vlan_create&dummy={int(time.time() * 1000)}"
            
            # Prepare the data payload (based on our previous successful test)
            vlan_list = f"1,105-106,110,120,130,140,150,160,170,180,190,{vlan_id}"
            data_payload = {
                f"_ds=1&vlanList={vlan_list}&_de=1": {}
            }
            
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
                'Origin': self.url,
                'Referer': f'{self.url}/html/vlan_vlan_create.html?_ver=3.1.0',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            response = self.session.post(create_url, json=data_payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('success') or 'logout' not in result:
                        self.console.print(f"[green]VLAN {vlan_id} created successfully![/green]")
                        
                        # Now update the VLAN name
                        return self._update_vlan_name(vlan_id, vlan_name)
                    else:
                        self.console.print(f"[red]VLAN creation failed: {result.get('reason', 'Unknown error')}[/red]")
                        return False
                except ValueError:
                    self.console.print("[red]Invalid response format from VLAN creation[/red]")
                    return False
            else:
                self.console.print(f"[red]VLAN creation failed: HTTP {response.status_code}[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error creating VLAN: {str(e)}[/red]")
            return False
    
    def _update_vlan_name(self, vlan_id: int, vlan_name: str) -> bool:
        """Update VLAN name after creation."""
        try:
            edit_url = f"{self.url}/cgi/set.cgi?cmd=vlan_edit&dummy={int(time.time() * 1000)}"
            
            data_payload = {
                f"_ds=1&vlanId={vlan_id}&vlanName={vlan_name}&_de=1": {}
            }
            
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/json',
                'Origin': self.url,
                'Referer': f'{self.url}/html/vlan_vlan_create.html?_ver=3.1.0',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            response = self.session.post(edit_url, json=data_payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('success') or 'logout' not in result:
                        self.console.print(f"[green]VLAN {vlan_id} name updated to '{vlan_name}'[/green]")
                        return True
                    else:
                        self.console.print(f"[yellow]VLAN created but name update failed: {result.get('reason', 'Unknown error')}[/yellow]")
                        return True  # VLAN was created, just name update failed
                except ValueError:
                    self.console.print("[yellow]VLAN created but name update response invalid[/yellow]")
                    return True  # VLAN was created, just name update failed
            else:
                self.console.print(f"[yellow]VLAN created but name update failed: HTTP {response.status_code}[/yellow]")
                return True  # VLAN was created, just name update failed
                
        except Exception as e:
            self.console.print(f"[yellow]VLAN created but name update error: {str(e)}[/yellow]")
            return True  # VLAN was created, just name update failed
    
    def delete_vlan(self, vlan_id: int) -> bool:
        """Delete a VLAN on VM-S100-0800MS switch."""
        try:
            # First authenticate
            if not self.authenticate():
                return False
            
            # Delete VLAN using the set.cgi endpoint
            delete_url = f"{self.url}/cgi/set.cgi?cmd=vlan_del&dummy={int(time.time() * 1000)}"
            
            # Prepare the data payload (based on our previous successful test)
            data_payload = {
                f"_ds=1&vlanList={vlan_id}&_de=1": {}
            }
            
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/json',
                'Origin': self.url,
                'Referer': f'{self.url}/html/vlan_vlan_create.html?_ver=3.1.0',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            response = self.session.post(delete_url, json=data_payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('success') or 'logout' not in result:
                        self.console.print(f"[green]VLAN {vlan_id} deleted successfully![/green]")
                        return True
                    else:
                        self.console.print(f"[red]VLAN deletion failed: {result.get('reason', 'Unknown error')}[/red]")
                        return False
                except ValueError:
                    self.console.print("[red]Invalid response format from VLAN deletion[/red]")
                    return False
            else:
                self.console.print(f"[red]VLAN deletion failed: HTTP {response.status_code}[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error deleting VLAN: {str(e)}[/red]")
            return False
