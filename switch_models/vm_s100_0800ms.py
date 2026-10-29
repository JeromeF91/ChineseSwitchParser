"""
VM-S100-0800MS switch model implementation.
This is the specific implementation for the VM-S100-0800MS switch model.
"""

import requests
import time
from typing import Dict, Any, Optional
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
            'line_config': 'cgi/get.cgi?cmd=line_conf',
            'lldp_neighbors': 'cgi/get.cgi?cmd=lldp_neighbor',
            'lldp_neighbor_detail': 'cgi/get.cgi?cmd=get_discoveryLldpNeighborDetail',
            'lldp_config': 'cgi/get.cgi?cmd=get_discoveryLldpConfig',
            'lldp_status': 'cgi/get.cgi?cmd=get_discoveryLldpStatus',
            'lldp_settings': 'cgi/get.cgi?cmd=get_discoveryLldpSettings',
            'lldp_global': 'cgi/get.cgi?cmd=get_discoveryLldpGlobal',
            'lldp_port': 'cgi/get.cgi?cmd=get_discoveryLldpPort',
            'lldp_port_config': 'cgi/get.cgi?cmd=get_discoveryLldpPortConfig'
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
    
    # ------------------------------------------------------------------
    # CGI write helpers
    #
    # All writes on this firmware go to cgi/set.cgi?cmd=<name> as
    # application/x-www-form-urlencoded bodies wrapped in a '_ds=1 ...
    # _de=1' envelope (this is what the web UI sends; JSON payloads are
    # silently rejected). Responses are:
    #   {"status":"ok", ...}                              -> applied
    #   {"status":"error","errMsgs":[...]}                -> rejected (partially applied in some cases!)
    #   {"logout":true,"reason":"timeout"}                -> session expired, write NOT applied
    # Sessions expire quickly; re-authenticate before each batch and
    # always read back state after writes.
    # ------------------------------------------------------------------

    def _form_post(self, cmd: str, pairs: list, referer_page: str = '') -> Optional[Dict[str, Any]]:
        """POST a form-urlencoded CGI command wrapped in the _ds/_de envelope.

        pairs: list of (key, value) tuples; repeated keys are allowed and
        sent in order (required for vlan_membershipEdit 'A' entries).
        Returns the parsed JSON response, or None on transport failure.
        """
        fields = [('_ds', '1')] + [(k, str(v)) for k, v in pairs] + [('_de', '1')]
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': self.url,
            'X-Requested-With': 'XMLHttpRequest',
        }
        if referer_page:
            headers['Referer'] = f'{self.url}/html/{referer_page}'
        post_url = f"{self.url}/cgi/set.cgi?cmd={cmd}&dummy={int(time.time() * 1000)}"
        response = self.session.post(post_url, data=fields, headers=headers, timeout=10)
        if response.status_code != 200:
            self.console.print(f"[red]CGI {cmd}: HTTP {response.status_code}[/red]")
            return None
        try:
            return response.json()
        except ValueError:
            self.console.print(f"[red]CGI {cmd}: invalid response: {response.text[:120]}[/red]")
            return None

    @staticmethod
    def _parse_write_response(result: Dict[str, Any]) -> tuple:
        """Return (ok, error_message) for a CGI write response."""
        if result.get('logout'):
            return False, f"session expired ({result.get('reason', 'timeout')}); write NOT applied"
        if result.get('status') == 'ok':
            return True, ''
        msgs = result.get('errMsgs') or result.get('msg') or result.get('reason') or 'unknown error'
        return False, str(msgs)

    def _form_get(self, cmd: str) -> Optional[Dict[str, Any]]:
        """GET a CGI command and return parsed JSON (data envelope stripped if present)."""
        get_url = f"{self.url}/cgi/get.cgi?cmd={cmd}&dummy={int(time.time() * 1000)}"
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
        }
        response = self.session.get(get_url, headers=headers, timeout=10)
        if response.status_code != 200:
            self.console.print(f"[red]CGI get {cmd}: HTTP {response.status_code}[/red]")
            return None
        try:
            payload = response.json()
        except ValueError:
            self.console.print(f"[red]CGI get {cmd}: invalid response[/red]")
            return None
        return payload.get('data', payload) if isinstance(payload, dict) else payload

    def get_current_vlan_ids(self) -> list:
        """Return the VLAN IDs currently defined on the switch."""
        if not self.authenticate():
            return []
        data = self._form_get('vlan_create')
        if not data:
            return []
        return sorted(int(v['vlan']) for v in data.get('adminVlans', []))

    @staticmethod
    def _parse_membership_string(membership: str) -> list:
        """Parse an adminVlans string like '1UP, 99T, 120T' into [(id, kind), ...].

        kind is 'T' (tagged), 'UP' (untagged/native) or 'F' (forbidden).
        The '4095P' hybrid placeholder entry is dropped.
        """
        entries = []
        for token in (membership or '').split(','):
            token = token.strip()
            if not token or token == '4095P':
                continue
            digits = ''.join(c for c in token if c.isdigit())
            kind = token[len(digits):]
            if digits and kind in ('T', 'UP', 'F'):
                entries.append((int(digits), kind))
        return entries

    def get_vlan_membership(self) -> list:
        """Return authoritative per-port VLAN membership.

        [{'port': <0-based index usable with vlan_membershipEdit>,
          'mode': <0 hybrid / 1 access / 2 trunk / 3 tunnel>,
          'entries': [(vlan_id, 'T'|'UP'|'F'), ...],
          'admin_vlans': <raw string>}, ...]
        """
        if not self.authenticate():
            return []
        data = self._form_get('vlan_membership')
        result = []
        for idx, port in enumerate((data or {}).get('ports', [])):
            result.append({
                'port': idx,
                'mode': port.get('mode'),
                'entries': self._parse_membership_string(port.get('adminVlans', '')),
                'admin_vlans': port.get('adminVlans', ''),
            })
        return result

    def _port_membership(self, port_index: int) -> list:
        """Return current membership entries [(id, kind), ...] for one port."""
        ports = self.get_vlan_membership()
        if port_index >= len(ports):
            raise ValueError(f"port index {port_index} out of range (0..{len(ports) - 1})")
        return ports[port_index]['entries']

    def create_vlan(self, vlan_id: int, vlan_name: str) -> bool:
        """Create a VLAN on VM-S100-0800MS switch and set its name.

        ⚠️ The vlan_create CGI is DECLARATIVE: vlanList is the COMPLETE set
        of VLANs that should exist — anything missing from the list is
        DELETED together with its port memberships. Only default VLAN 1 and
        the management VLAN are protected by the firmware. This method
        therefore always sends (current set ∪ {vlan_id}); never replace
        that with a hardcoded list.
        """
        try:
            if not self.authenticate():
                return False

            current = self.get_current_vlan_ids()
            if not current:
                self.console.print("[red]Could not read current VLAN set; refusing to write (vlan_create is declarative)[/red]")
                return False

            if vlan_id in current:
                self.console.print(f"[yellow]VLAN {vlan_id} already exists; updating name only[/yellow]")
                return self._update_vlan_name(vlan_id, vlan_name)

            wanted = sorted(set(current) | {vlan_id})
            result = self._form_post('vlan_create',
                                     [('vlanList', ','.join(str(v) for v in wanted))],
                                     'vlan_vlan_create.html')
            if result is None:
                return False
            ok, err = self._parse_write_response(result)
            if not ok:
                # error responses can be partially applied; verify actual state
                if vlan_id in self.get_current_vlan_ids():
                    self.console.print(f"[yellow]vlan_create reported '{err}' but VLAN {vlan_id} exists; continuing[/yellow]")
                else:
                    self.console.print(f"[red]VLAN {vlan_id} creation failed: {err}[/red]")
                    return False
            self.console.print(f"[green]VLAN {vlan_id} created successfully![/green]")
            return self._update_vlan_name(vlan_id, vlan_name)

        except Exception as e:
            self.console.print(f"[red]Error creating VLAN: {str(e)}[/red]")
            return False

    def _update_vlan_name(self, vlan_id: int, vlan_name: str) -> bool:
        """Set a VLAN's name (vlan_edit expects 'vlan' and 'name' fields)."""
        try:
            result = self._form_post('vlan_edit',
                                     [('vlan', vlan_id), ('name', vlan_name)],
                                     'vlan_vlan_edit.html')
            if result is None:
                return False
            ok, err = self._parse_write_response(result)
            if not ok:
                # firmware rejects duplicate names, including renaming a VLAN
                # to the name it already has — verify intended state instead
                data = self._form_get('vlan_create') or {}
                for v in data.get('adminVlans', []):
                    if int(v['vlan']) == vlan_id and v.get('name') == vlan_name:
                        self.console.print(f"[green]VLAN {vlan_id} already named '{vlan_name}'[/green]")
                        return True
                self.console.print(f"[yellow]VLAN {vlan_id} name update failed: {err}[/yellow]")
                return False
            self.console.print(f"[green]VLAN {vlan_id} name set to '{vlan_name}'[/green]")
            return True
        except Exception as e:
            self.console.print(f"[yellow]VLAN {vlan_id} name update error: {str(e)}[/yellow]")
            return False

    def delete_vlan(self, vlan_id: int) -> bool:
        """Delete a VLAN on VM-S100-0800MS switch.

        Implemented via the proven declarative path: vlan_create with the
        full set MINUS the target. (The standalone 'vlan_del' command was
        never observed working and is not used.) Firmware refuses to delete
        default VLAN 1 and the management VLAN.
        """
        try:
            if not self.authenticate():
                return False

            current = self.get_current_vlan_ids()
            if vlan_id not in current:
                self.console.print(f"[yellow]VLAN {vlan_id} does not exist; nothing to delete[/yellow]")
                return True

            remaining = sorted(set(current) - {vlan_id})
            result = self._form_post('vlan_create',
                                     [('vlanList', ','.join(str(v) for v in remaining))],
                                     'vlan_vlan_create.html')
            if result is None:
                return False
            ok, err = self._parse_write_response(result)
            if vlan_id in self.get_current_vlan_ids():
                self.console.print(f"[red]VLAN {vlan_id} deletion failed: {err or 'still present after write'}[/red]")
                return False
            self.console.print(f"[green]VLAN {vlan_id} deleted successfully![/green]")
            return True

        except Exception as e:
            self.console.print(f"[red]Error deleting VLAN: {str(e)}[/red]")
            return False

    def set_port_vlan_membership(self, port_index: int, entries: list, verify: bool = True) -> bool:
        """Replace the COMPLETE VLAN membership of one port.

        port_index: 0-based index into get_vlan_membership().
        entries: iterable of (vlan_id, kind) with kind in
                 {'T': tagged, 'UP': untagged/native, 'F': forbidden}.

        ⚠️ Declarative per port: the posted list becomes the port's full
        membership — omitted VLANs are removed from the port. Preserve the
        native (UP) entry and the management VLAN or you can lose the
        switch's own reachability. Use add_port_to_vlan /
        remove_port_from_vlan for safe incremental changes.
        """
        try:
            if not self.authenticate():
                return False

            formatted = sorted({(int(vid), kind) for vid, kind in entries})
            for _vid, kind in formatted:
                if kind not in ('T', 'UP', 'F'):
                    self.console.print(f"[red]invalid kind '{kind}' (use 'T', 'UP' or 'F')[/red]")
                    return False

            pairs = [('port', port_index)] + [('A', f'{vid}{kind}') for vid, kind in formatted]
            result = self._form_post('vlan_membershipEdit', pairs, 'vlan_vlan_membership.html')
            if result is None:
                return False
            ok, err = self._parse_write_response(result)
            if not ok:
                self.console.print(f"[red]port {port_index} membership write failed: {err}[/red]")
                return False

            if verify:
                actual = sorted(self._port_membership(port_index))
                if actual != formatted:
                    self.console.print(f"[red]port {port_index} read-back mismatch: expected {formatted}, got {actual}[/red]")
                    return False
            self.console.print(f"[green]port {port_index} membership set: {formatted}[/green]")
            return True

        except Exception as e:
            self.console.print(f"[red]Error setting port membership: {str(e)}[/red]")
            return False

    def add_port_to_vlan(self, port_index: int, vlan_id: int, tagged: bool = True) -> bool:
        """Add one port to one VLAN incrementally (keeps all other entries)."""
        try:
            current = self._port_membership(port_index)
            kind = 'T' if tagged else 'UP'
            wanted = {(vid, k) for vid, k in current if vid != vlan_id}
            wanted.add((vlan_id, kind))
            return self.set_port_vlan_membership(port_index, sorted(wanted))
        except Exception as e:
            self.console.print(f"[red]Error adding port {port_index} to VLAN {vlan_id}: {str(e)}[/red]")
            return False

    def remove_port_from_vlan(self, port_index: int, vlan_id: int) -> bool:
        """Remove one port from one VLAN incrementally (keeps all other entries)."""
        try:
            current = self._port_membership(port_index)
            wanted = {(vid, k) for vid, k in current if vid != vlan_id}
            if len(wanted) == len(current):
                self.console.print(f"[yellow]port {port_index} is not a member of VLAN {vlan_id}; nothing to remove[/yellow]")
                return True
            return self.set_port_vlan_membership(port_index, sorted(wanted))
        except Exception as e:
            self.console.print(f"[red]Error removing port {port_index} from VLAN {vlan_id}: {str(e)}[/red]")
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
        """Save running configuration to flash (home_save)."""
        try:
            if not self.authenticate():
                return False

            result = self._form_post('home_save', [], 'system.html')
            if result is None:
                return False
            ok, err = self._parse_write_response(result)
            if not ok:
                self.console.print(f"[red]Configuration save failed: {err}[/red]")
                return False
            self.console.print("[green]Configuration saved successfully![/green]")
            return True

        except Exception as e:
            self.console.print(f"[red]Error saving configuration: {str(e)}[/red]")
            return False
    
    def _parse_lldp_neighbors(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLDP neighbor information."""
        neighbors = []
        
        if 'data' in data and 'neighbors' in data['data']:
            for neighbor in data['data']['neighbors']:
                neighbor_info = {
                    'local_port': neighbor.get('localPort', ''),
                    'chassis_id': neighbor.get('chassisId', ''),
                    'chassis_type': neighbor.get('chassisType', ''),
                    'port_id': neighbor.get('portId', ''),
                    'port_id_type': neighbor.get('portIdType', ''),
                    'system_name': neighbor.get('sysName', ''),
                    'ttl': neighbor.get('ttl', 0),
                    'index': neighbor.get('index', 0)
                }
                neighbors.append(neighbor_info)
        
        return {
            'neighbors': neighbors,
            'neighbor_count': len(neighbors)
        }
    
    def _parse_lldp_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLDP configuration information."""
        config = {}
        
        if 'data' in data:
            config = data['data']
        
        return config
    
    def _parse_lldp_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLDP status information."""
        status = {}
        
        if 'data' in data:
            status = data['data']
        
        return status
    
    def get_data(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get data from a specific API endpoint with LLDP parsing."""
        try:
            url = f"{self.url}/{endpoint}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Parse LLDP-specific endpoints
                    if 'cmd=lldp_neighbor' in endpoint:
                        return self._parse_lldp_neighbors(data)
                    elif 'cmd=lldp_config' in endpoint or 'cmd=get_discoveryLldpConfig' in endpoint:
                        return self._parse_lldp_config(data)
                    elif 'cmd=lldp_status' in endpoint or 'cmd=get_discoveryLldpStatus' in endpoint:
                        return self._parse_lldp_status(data)
                    else:
                        # For other endpoints, return data as-is
                        return data
                        
                except ValueError:
                    # If not JSON, return as text
                    return {"data": response.text}
            else:
                logger.warning(f"Failed to get data from {endpoint}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting data from {endpoint}: {str(e)}")
            return None
