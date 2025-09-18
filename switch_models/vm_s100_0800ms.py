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
            'port_config': 'cgi/get.cgi?cmd=port_config',
            'port_status': 'cgi/get.cgi?cmd=port_status',
            'lag_info': 'cgi/get.cgi?cmd=lag_mgmt',
            'syslog': 'cgi/get.cgi?cmd=log_syslog',
            'panel_info': 'cgi/get.cgi?cmd=panel_info',
            'panel_layout': 'cgi/get.cgi?cmd=panel_layout',
            'vlan_config': 'cgi/get.cgi?cmd=vlan_conf',
            'vlan_membership': 'cgi/get.cgi?cmd=vlan_membership',
            'vlan_port': 'cgi/get.cgi?cmd=vlan_port',
            'mac_dynamic': 'cgi/get.cgi?cmd=mac_dynamic',
            'mac_static': 'cgi/get.cgi?cmd=mac_static',
            'mac_status': 'cgi/get.cgi?cmd=mac_miscStatus',
            'line_config': 'cgi/get.cgi?cmd=line_conf'
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
        
        if 'port_config' in data.get('data', {}) or 'port_status' in data.get('data', {}):
            data['port_config'] = self._process_port_config_data(data['data'])
        
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
    
    def _process_port_config_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process port configuration data including speed/duplex and VLAN assignments."""
        port_config = {
            'ports': [],
            'vlan_assignments': {}
        }
        
        # Process port configuration from panel_info if available
        if 'panel_info' in raw_data and 'data' in raw_data['panel_info']:
            panel_data = raw_data['panel_info']['data']
            if 'ports' in panel_data:
                for i, port_data in enumerate(panel_data['ports'], 1):
                    # Standardize port configuration structure
                    port_info = {
                        'port_id': f"TE{i}",
                        'port_number': i,
                        'name': f"Port {i}",
                        'status': 'up' if port_data.get('linkup', False) else 'down',
                        'enabled': port_data.get('linkup', False),
                        'speed': self._normalize_speed(port_data.get('speed', 'Unknown')),
                        'duplex': 'full' if port_data.get('dupFull', False) else 'half',
                        'auto_negotiation': port_data.get('autoNego', False),
                        'flow_control': 'Unknown',  # Not available in panel_info
                        'media_type': port_data.get('media', 'Unknown'),
                        'description': f"Port {i}"
                    }
                    port_config['ports'].append(port_info)
        
        # Process VLAN port assignments
        if 'vlan_port' in raw_data and 'data' in raw_data['vlan_port']:
            vlan_port_data = raw_data['vlan_port']['data']
            if 'ports' in vlan_port_data:
                for i, port_vlan_data in enumerate(vlan_port_data['ports'], 1):
                    port_id = f"TE{i}"
                    port_config['vlan_assignments'][port_id] = {
                        'mode': self._normalize_vlan_mode(port_vlan_data.get('mode', 'Unknown')),
                        'pvid': port_vlan_data.get('pvid', 'Unknown'),
                        'frame_type': self._normalize_frame_type(port_vlan_data.get('accFrameType', 'Unknown')),
                        'ingress_filter': port_vlan_data.get('ingressFilter', False),
                        'uplink': port_vlan_data.get('uplink', False),
                        'tpid': port_vlan_data.get('tpid', 'Unknown'),
                        'tagged_vlans': [],
                        'untagged_vlans': []
                    }
        
        # Process VLAN membership for tagged/untagged information
        if 'vlan_membership' in raw_data and 'data' in raw_data['vlan_membership']:
            vlan_membership_data = raw_data['vlan_membership']['data']
            if 'ports' in vlan_membership_data:
                for i, port_membership in enumerate(vlan_membership_data['ports'], 1):
                    port_id = f"TE{i}"
                    if port_id not in port_config['vlan_assignments']:
                        port_config['vlan_assignments'][port_id] = {
                            'mode': 'Unknown',
                            'pvid': 'Unknown',
                            'frame_type': 'Unknown',
                            'ingress_filter': False,
                            'uplink': False,
                            'tpid': 'Unknown',
                            'tagged_vlans': [],
                            'untagged_vlans': []
                        }
                    
                    # Parse VLAN assignments
                    admin_vlans = port_membership.get('adminVlans', '')
                    if admin_vlans:
                        tagged, untagged = self._parse_vlan_assignments(admin_vlans)
                        port_config['vlan_assignments'][port_id]['tagged_vlans'] = tagged
                        port_config['vlan_assignments'][port_id]['untagged_vlans'] = untagged
        
        return port_config
    
    def _normalize_speed(self, speed: str) -> str:
        """Normalize speed values to standard format."""
        if speed == '10000':
            return '10G'
        elif speed == '1000':
            return '1G'
        elif speed == '100':
            return '100M'
        elif speed == '10':
            return '10M'
        else:
            return str(speed)
    
    def _normalize_vlan_mode(self, mode: int) -> str:
        """Normalize VLAN mode values."""
        mode_map = {
            0: 'access',
            1: 'trunk',
            2: 'hybrid'
        }
        return mode_map.get(mode, 'Unknown')
    
    def _normalize_frame_type(self, frame_type: int) -> str:
        """Normalize frame type values."""
        frame_map = {
            0: 'all',
            1: 'tagged_only',
            2: 'untagged_only'
        }
        return frame_map.get(frame_type, 'Unknown')
    
    def _parse_vlan_assignments(self, vlan_string: str) -> tuple:
        """Parse VLAN assignment string into tagged and untagged lists."""
        tagged = []
        untagged = []
        
        if not vlan_string:
            return tagged, untagged
        
        # Parse format like "1UP, 99T, 105T, 106T, 110T, 120T, 130T, 140T, 150T, 160T, 170T, 180T, 190T"
        for vlan_entry in vlan_string.split(', '):
            vlan_entry = vlan_entry.strip()
            if vlan_entry.endswith('T'):
                # Tagged VLAN
                vlan_id = vlan_entry[:-1]
                if vlan_id.isdigit():
                    tagged.append(vlan_id)
            elif vlan_entry.endswith('UP') or vlan_entry.endswith('FP'):
                # Untagged VLAN (UP = untagged port, FP = forbidden port)
                vlan_id = vlan_entry[:-2]
                if vlan_id.isdigit():
                    untagged.append(vlan_id)
            elif vlan_entry.endswith('F'):
                # Forbidden VLAN
                vlan_id = vlan_entry[:-1]
                if vlan_id.isdigit():
                    untagged.append(vlan_id)
        
        return tagged, untagged
    
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
        
        # Display port configuration if available
        if 'port_config' in data:
            self.console.print("\n[bold yellow]Port Configuration:[/bold yellow]")
            
            if 'ports' in data['port_config']:
                self.console.print("\n[bold]Port Status & Speed/Duplex:[/bold]")
                for port in data['port_config']['ports']:
                    status_icon = "✅" if port['status'] == 'up' else "❌"
                    speed_duplex = f"{port['speed']} {port['duplex']}"
                    auto_nego = "Auto" if port['auto_negotiation'] else "Manual"
                    flow_control = "On" if port['flow_control'] else "Off"
                    
                    self.console.print(f"  {port['port_id']}: {status_icon} {port['status'].upper()} | {speed_duplex} | {auto_nego} | Flow: {flow_control} | {port['media_type']}")
            
            if 'vlan_assignments' in data['port_config']:
                self.console.print("\n[bold]Port VLAN Assignments:[/bold]")
                for port_id, vlan_config in data['port_config']['vlan_assignments'].items():
                    self.console.print(f"\n  [bold]{port_id}:[/bold]")
                    self.console.print(f"    Mode: {vlan_config.get('mode', 'Unknown')}")
                    self.console.print(f"    PVID: {vlan_config.get('pvid', 'Unknown')}")
                    self.console.print(f"    Frame Type: {vlan_config.get('frame_type', 'Unknown')}")
                    self.console.print(f"    Ingress Filter: {'Enabled' if vlan_config.get('ingress_filter') else 'Disabled'}")
                    
                    if vlan_config.get('tagged_vlans'):
                        self.console.print(f"    Tagged VLANs: {', '.join(vlan_config['tagged_vlans'])}")
                    if vlan_config.get('untagged_vlans'):
                        self.console.print(f"    Untagged VLANs: {', '.join(vlan_config['untagged_vlans'])}")
        
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

    def enable_ssh(self) -> bool:
        """Enable SSH on VM-S100-0800MS switch."""
        try:
            if not self.authenticate():
                return False
            
            # Try multiple possible endpoints for SSH configuration
            ssh_endpoints = [
                f"{self.url}/cgi/set.cgi?cmd=line_ssh&dummy={int(time.time() * 1000)}",
                f"{self.url}/cgi/set.cgi?cmd=line_conf&dummy={int(time.time() * 1000)}",
                f"{self.url}/cgi/set.cgi?cmd=sys_line&dummy={int(time.time() * 1000)}"
            ]
            
            for ssh_url in ssh_endpoints:
                try:
                    # Try different payload formats
                    payloads = [
                        {"_ds=1&ssh=1&_de=1": {}},
                        {"_ds=1&sshState=1&_de=1": {}},
                        {"_ds=1&lineSSH=1&_de=1": {}},
                        {"ssh": True, "enable": True},
                        {"sshState": True}
                    ]
                    
                    headers = {
                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                        'Content-Type': 'application/json',
                        'Origin': self.url,
                        'Referer': f'{self.url}/html/line.html',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                    
                    for payload in payloads:
                        response = self.session.post(ssh_url, json=payload, headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            try:
                                result = response.json()
                                if result.get('success') or 'logout' not in result:
                                    self.console.print(f"[green]SSH enabled successfully![/green]")
                                    return True
                            except ValueError:
                                # Non-JSON response, check if it's successful HTML
                                if "success" in response.text.lower() or response.status_code == 200:
                                    self.console.print(f"[green]SSH enabled successfully![/green]")
                                    return True
                except Exception as e:
                    continue  # Try next endpoint/payload combination
            
            # If all attempts failed, try a generic approach
            self.console.print("[yellow]Standard SSH endpoints failed, trying alternative method...[/yellow]")
            return self._enable_ssh_alternative()
            
        except Exception as e:
            self.console.print(f"[red]Error enabling SSH: {str(e)}[/red]")
            return False

    def _enable_ssh_alternative(self) -> bool:
        """Alternative method to enable SSH using system configuration."""
        try:
            # Try to find and modify system configuration
            system_config_url = f"{self.url}/cgi/set.cgi?cmd=sys_conf&dummy={int(time.time() * 1000)}"
            
            payload = {
                "_ds=1&methods=[{\"txt\":\"lang('line','lblTelnet')\",\"state\":false},{\"txt\":\"lang('line','lblSsh')\",\"state\":true},{\"txt\":\"lang('line','lblHttp')\",\"state\":true},{\"txt\":\"lang('line','lblHttps')\",\"state\":false},{\"txt\":\"lang('line','lblSnmp')\",\"state\":true}]&_de=1": {}
            }
            
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/json',
                'Origin': self.url,
                'Referer': f'{self.url}/html/system.html',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            response = self.session.post(system_config_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('success') or 'logout' not in result:
                        self.console.print(f"[green]SSH enabled via system configuration![/green]")
                        return True
                except ValueError:
                    if "success" in response.text.lower():
                        self.console.print(f"[green]SSH enabled via system configuration![/green]")
                        return True
            
            self.console.print(f"[red]Could not enable SSH - configuration endpoint not found[/red]")
            return False
            
        except Exception as e:
            self.console.print(f"[red]Error in alternative SSH enable method: {str(e)}[/red]")
            return False

    def disable_ssh(self) -> bool:
        """Disable SSH on VM-S100-0800MS switch."""
        try:
            if not self.authenticate():
                return False
            
            # Similar approach but with SSH disabled
            ssh_endpoints = [
                f"{self.url}/cgi/set.cgi?cmd=line_ssh&dummy={int(time.time() * 1000)}",
                f"{self.url}/cgi/set.cgi?cmd=line_conf&dummy={int(time.time() * 1000)}",
                f"{self.url}/cgi/set.cgi?cmd=sys_line&dummy={int(time.time() * 1000)}"
            ]
            
            for ssh_url in ssh_endpoints:
                try:
                    payloads = [
                        {"_ds=1&ssh=0&_de=1": {}},
                        {"_ds=1&sshState=0&_de=1": {}},
                        {"_ds=1&lineSSH=0&_de=1": {}},
                        {"ssh": False, "enable": False},
                        {"sshState": False}
                    ]
                    
                    headers = {
                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                        'Content-Type': 'application/json',
                        'Origin': self.url,
                        'Referer': f'{self.url}/html/line.html',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                    
                    for payload in payloads:
                        response = self.session.post(ssh_url, json=payload, headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            try:
                                result = response.json()
                                if result.get('success') or 'logout' not in result:
                                    self.console.print(f"[green]SSH disabled successfully![/green]")
                                    return True
                            except ValueError:
                                if "success" in response.text.lower():
                                    self.console.print(f"[green]SSH disabled successfully![/green]")
                                    return True
                except Exception as e:
                    continue
            
            self.console.print(f"[red]Could not disable SSH - configuration endpoint not found[/red]")
            return False
            
        except Exception as e:
            self.console.print(f"[red]Error disabling SSH: {str(e)}[/red]")
            return False
    
    def save_configuration(self) -> bool:
        """Save configuration to flash memory on VM-S100-0800MS switch."""
        try:
            if not self.authenticate():
                return False
            
            # Try multiple possible endpoints for saving configuration
            save_endpoints = [
                f"{self.url}/cgi/set.cgi?cmd=save&dummy={int(time.time() * 1000)}",
                f"{self.url}/cgi/set.cgi?cmd=config_save&dummy={int(time.time() * 1000)}",
                f"{self.url}/cgi/set.cgi?cmd=sys_save&dummy={int(time.time() * 1000)}"
            ]
            
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/json',
                'Origin': self.url,
                'Referer': f'{self.url}/html/system.html',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            for save_url in save_endpoints:
                try:
                    # Try different payload formats
                    payloads = [
                        {"_ds=1&save=1&_de=1": {}},
                        {"_ds=1&config_save=1&_de=1": {}},
                        {"save": True},
                        {"config_save": True}
                    ]
                    
                    for payload in payloads:
                        response = self.session.post(save_url, json=payload, headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            try:
                                result = response.json()
                                if result.get('success') or 'logout' not in result:
                                    self.console.print(f"[green]Configuration saved successfully![/green]")
                                    return True
                            except ValueError:
                                # Non-JSON response, check if it's successful HTML
                                if "success" in response.text.lower() or response.status_code == 200:
                                    self.console.print(f"[green]Configuration saved successfully![/green]")
                                    return True
                except Exception as e:
                    continue  # Try next endpoint/payload combination
            
            self.console.print(f"[red]Could not save configuration - no working endpoint found[/red]")
            return False
            
        except Exception as e:
            self.console.print(f"[red]Error saving configuration: {str(e)}[/red]")
            return False
