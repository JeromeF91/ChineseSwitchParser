#!/usr/bin/env python3
"""
Final Chinese Switch Parser

This parser properly authenticates and then accesses the real API endpoints
to extract actual switch data.
"""

import requests
import json
import time
import re
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import click
import threading
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinalChineseSwitchParser:
    """Final parser that accesses real API endpoints."""
    
    def __init__(self, base_url: str, username: str = None, password: str = None):
        """Initialize the parser."""
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.console = Console()
        self.session = requests.Session()
        
        # Set up session headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.is_authenticated = False
        
        # MAC vendor lookup cache and rate limiting
        self.mac_vendor_cache = {}
        self.mac_lookup_lock = threading.Lock()
        self.last_mac_lookup_time = 0
        self.mac_lookup_delay = 1.0  # 1 second delay between lookups
        
        self.api_endpoints = {
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
    
    def connect(self) -> bool:
        """Connect and authenticate with the switch."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Connecting to switch...", total=None)
                
                # First, get the login page
                progress.update(task, description="Loading login page...")
                login_url = f"{self.base_url}/login.html"
                response = self.session.get(login_url, timeout=10)
                
                if response.status_code != 200:
                    self.console.print(f"[red]Failed to access login page. Status: {response.status_code}[/red]")
                    return False
                
                progress.update(task, description="Authenticating...")
                
                # Try to authenticate using the login API
                if self.username and self.password:
                    return self._authenticate_via_api()
                else:
                    self.console.print("[yellow]No credentials provided. Trying to access without authentication...[/yellow]")
                    return self._try_access_without_auth()
                    
        except Exception as e:
            self.console.print(f"[red]Connection error: {str(e)}[/red]")
            logger.error(f"Connection error: {str(e)}")
            return False
    
    def _authenticate_via_api(self) -> bool:
        """Authenticate using the login API."""
        try:
            # Try the login authentication API
            auth_url = f"{self.base_url}/cgi/set.cgi?cmd=home_loginAuth"
            
            # Prepare authentication data
            auth_data = {
                'username': self.username,
                'password': self.password
            }
            
            # Try to authenticate
            response = self.session.post(auth_url, data=auth_data, timeout=10)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('success') or 'logout' not in result:
                        self.is_authenticated = True
                        self.console.print("[green]Authentication successful![/green]")
                        return True
                    else:
                        self.console.print(f"[red]Authentication failed: {result.get('reason', 'Unknown error')}[/red]")
                        return False
                except:
                    # If not JSON, check if we got redirected or got success content
                    if 'login' not in response.url.lower() or 'success' in response.text.lower():
                        self.is_authenticated = True
                        self.console.print("[green]Authentication successful![/green]")
                        return True
                    else:
                        self.console.print("[red]Authentication failed - invalid response[/red]")
                        return False
            else:
                self.console.print(f"[red]Authentication failed with status: {response.status_code}[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Authentication error: {str(e)}[/red]")
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def _try_access_without_auth(self) -> bool:
        """Try to access switch data without authentication."""
        try:
            # Try to access the main page
            main_url = f"{self.base_url}/home.html"
            response = self.session.get(main_url, timeout=10)
            
            if response.status_code == 200 and 'login' not in response.url.lower():
                self.is_authenticated = True
                self.console.print("[green]Access successful without authentication[/green]")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error trying access without auth: {str(e)}")
            return False
    
    def get_comprehensive_data(self) -> Dict[str, Any]:
        """Get comprehensive switch data from API endpoints."""
        if not self.is_authenticated:
            self.console.print("[red]Not authenticated. Please connect first.[/red]")
            return {}
        
        data = {
            'system_info': self._get_system_info(),
            'port_status': self._get_port_status(),
            'vlan_info': self._get_vlan_info(),
            'mac_table': self._get_mac_address_table(),
            'cpu_memory': self._get_cpu_memory(),
            'network_stats': self._get_network_stats(),
            'exported_at': time.strftime("%Y-%m-%d %H:%M:%S"),
            'switch_url': self.base_url
        }
        
        return data
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information from API."""
        try:
            url = f"{self.base_url}/{self.api_endpoints['system_info']}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'logout' not in data:
                        self.console.print("[green]System info retrieved successfully[/green]")
                        return data
                    else:
                        self.console.print("[yellow]System info requires authentication[/yellow]")
                        return {}
                except:
                    self.console.print("[yellow]System info response is not JSON[/yellow]")
                    return {}
            else:
                self.console.print(f"[yellow]System info request failed: {response.status_code}[/yellow]")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return {}
    
    def _get_port_status(self) -> List[Dict[str, Any]]:
        """Get port status information."""
        ports = []
        
        try:
            # Get port count
            url = f"{self.base_url}/{self.api_endpoints['port_count']}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'logout' not in data:
                        self.console.print("[green]Port count retrieved successfully[/green]")
                        ports.append(data)
                    else:
                        self.console.print("[yellow]Port count requires authentication[/yellow]")
                except:
                    self.console.print("[yellow]Port count response is not JSON[/yellow]")
            
            # Get port bandwidth utilization
            url = f"{self.base_url}/{self.api_endpoints['port_bandwidth']}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'logout' not in data:
                        self.console.print("[green]Port bandwidth retrieved successfully[/green]")
                        ports.append(data)
                    else:
                        self.console.print("[yellow]Port bandwidth requires authentication[/yellow]")
                except:
                    self.console.print("[yellow]Port bandwidth response is not JSON[/yellow]")
            
            if ports:
                self.console.print(f"[green]Retrieved {len(ports)} port-related data sets[/green]")
            else:
                self.console.print("[yellow]No port information available[/yellow]")
                
        except Exception as e:
            logger.error(f"Error getting port status: {str(e)}")
        
        return ports
    
    def _get_vlan_info(self) -> List[Dict[str, Any]]:
        """Get VLAN information."""
        vlans = []
        
        try:
            # Get VLAN configuration
            url = f"{self.base_url}/{self.api_endpoints['vlan_config']}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'logout' not in data and 'data' in data:
                        self.console.print("[green]VLAN configuration retrieved successfully[/green]")
                        vlans.append({
                            'type': 'vlan_config',
                            'data': data['data']
                        })
                    else:
                        self.console.print("[yellow]VLAN config requires authentication[/yellow]")
                except:
                    self.console.print("[yellow]VLAN config response is not JSON[/yellow]")
            
            # Get VLAN membership
            url = f"{self.base_url}/{self.api_endpoints['vlan_membership']}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'logout' not in data and 'data' in data:
                        self.console.print("[green]VLAN membership retrieved successfully[/green]")
                        vlans.append({
                            'type': 'vlan_membership',
                            'data': data['data']
                        })
                    else:
                        self.console.print("[yellow]VLAN membership requires authentication[/yellow]")
                except:
                    self.console.print("[yellow]VLAN membership response is not JSON[/yellow]")
            
            if vlans:
                self.console.print(f"[green]Retrieved {len(vlans)} VLAN data sets[/green]")
            else:
                self.console.print("[yellow]No VLAN information available[/yellow]")
                
        except Exception as e:
            logger.error(f"Error getting VLAN info: {str(e)}")
        
        return vlans
    
    def _get_mac_address_table(self) -> List[Dict[str, Any]]:
        """Get MAC address table information."""
        mac_data = []
        
        try:
            # Get dynamic MAC addresses
            url = f"{self.base_url}/{self.api_endpoints['mac_dynamic']}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'logout' not in data and 'data' in data:
                        self.console.print("[green]Dynamic MAC addresses retrieved successfully[/green]")
                        mac_data.append({
                            'type': 'dynamic_mac',
                            'data': data['data']
                        })
                    else:
                        self.console.print("[yellow]Dynamic MAC addresses require authentication[/yellow]")
                except:
                    self.console.print("[yellow]Dynamic MAC addresses response is not JSON[/yellow]")
            
            # Get static MAC addresses
            url = f"{self.base_url}/{self.api_endpoints['mac_static']}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'logout' not in data and 'data' in data:
                        self.console.print("[green]Static MAC addresses retrieved successfully[/green]")
                        mac_data.append({
                            'type': 'static_mac',
                            'data': data['data']
                        })
                    else:
                        self.console.print("[yellow]Static MAC addresses require authentication[/yellow]")
                except:
                    self.console.print("[yellow]Static MAC addresses response is not JSON[/yellow]")
            
            # Get MAC status information
            url = f"{self.base_url}/{self.api_endpoints['mac_status']}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'logout' not in data and 'data' in data:
                        self.console.print("[green]MAC status information retrieved successfully[/green]")
                        mac_data.append({
                            'type': 'mac_status',
                            'data': data['data']
                        })
                    else:
                        self.console.print("[yellow]MAC status information requires authentication[/yellow]")
                except:
                    self.console.print("[yellow]MAC status information response is not JSON[/yellow]")
            
            if mac_data:
                self.console.print(f"[green]Retrieved {len(mac_data)} MAC address data sets[/green]")
            else:
                self.console.print("[yellow]No MAC address information available[/yellow]")
                
        except Exception as e:
            logger.error(f"Error getting MAC address table: {str(e)}")
        
        return mac_data
    
    def _resolve_mac_vendor(self, mac_address: str) -> str:
        """Resolve MAC address to vendor using MACVendors.com API with caching and rate limiting."""
        try:
            # Clean MAC address (remove colons, dashes, etc.)
            clean_mac = re.sub(r'[^0-9A-Fa-f]', '', mac_address.upper())
            
            # Take first 6 characters (OUI)
            oui = clean_mac[:6]
            
            if len(oui) != 6:
                return "Invalid MAC"
            
            # Check cache first
            with self.mac_lookup_lock:
                if oui in self.mac_vendor_cache:
                    return self.mac_vendor_cache[oui]
                
                # Rate limiting: wait if we've made a request too recently
                current_time = time.time()
                time_since_last_lookup = current_time - self.last_mac_lookup_time
                
                if time_since_last_lookup < self.mac_lookup_delay:
                    sleep_time = self.mac_lookup_delay - time_since_last_lookup
                    time.sleep(sleep_time)
                
                # Update last lookup time
                self.last_mac_lookup_time = time.time()
            
            # Use MACVendors.com API
            url = f"https://api.macvendors.com/{mac_address}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                vendor = response.text.strip()
                if vendor and not vendor.startswith("Not Found"):
                    # Cache the result
                    with self.mac_lookup_lock:
                        self.mac_vendor_cache[oui] = vendor
                    return vendor
                else:
                    # Cache unknown result
                    with self.mac_lookup_lock:
                        self.mac_vendor_cache[oui] = "Unknown Vendor"
                    return "Unknown Vendor"
            elif response.status_code == 404:
                # MAC address not found in database
                with self.mac_lookup_lock:
                    self.mac_vendor_cache[oui] = "Unregistered OUI"
                return "Unregistered OUI"
            elif response.status_code == 429:  # Rate limited
                # Increase delay for next requests
                self.mac_lookup_delay = min(self.mac_lookup_delay * 2, 10.0)
                with self.mac_lookup_lock:
                    self.mac_vendor_cache[oui] = "Rate Limited"
                return "Rate Limited"
            else:
                with self.mac_lookup_lock:
                    self.mac_vendor_cache[oui] = "API Error"
                return "API Error"
                
        except Exception as e:
            logger.error(f"Error resolving MAC vendor for {mac_address}: {str(e)}")
            with self.mac_lookup_lock:
                self.mac_vendor_cache[clean_mac[:6]] = "Lookup Failed"
            return "Lookup Failed"
    
    def get_mac_cache_stats(self) -> Dict[str, Any]:
        """Get MAC vendor cache statistics."""
        with self.mac_lookup_lock:
            return {
                'cache_size': len(self.mac_vendor_cache),
                'cached_ouis': list(self.mac_vendor_cache.keys()),
                'current_delay': self.mac_lookup_delay,
                'last_lookup_time': self.last_mac_lookup_time
            }
    
    def clear_mac_cache(self):
        """Clear the MAC vendor cache."""
        with self.mac_lookup_lock:
            self.mac_vendor_cache.clear()
            self.last_mac_lookup_time = 0
            self.mac_lookup_delay = 1.0
    
    def _get_cpu_memory(self) -> Dict[str, Any]:
        """Get CPU and memory information."""
        try:
            url = f"{self.base_url}/{self.api_endpoints['cpu_memory']}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'logout' not in data:
                        self.console.print("[green]CPU/Memory info retrieved successfully[/green]")
                        return data
                    else:
                        self.console.print("[yellow]CPU/Memory info requires authentication[/yellow]")
                        return {}
                except:
                    self.console.print("[yellow]CPU/Memory info response is not JSON[/yellow]")
                    return {}
            else:
                self.console.print(f"[yellow]CPU/Memory info request failed: {response.status_code}[/yellow]")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting CPU/Memory info: {str(e)}")
            return {}
    
    def _get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics."""
        stats = {}
        
        try:
            # Get panel info
            url = f"{self.base_url}/{self.api_endpoints['panel_info']}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'logout' not in data:
                        stats['panel_info'] = data
                        self.console.print("[green]Panel info retrieved successfully[/green]")
                    else:
                        self.console.print("[yellow]Panel info requires authentication[/yellow]")
                except:
                    self.console.print("[yellow]Panel info response is not JSON[/yellow]")
            
            # Get syslog
            url = f"{self.base_url}/{self.api_endpoints['syslog']}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'logout' not in data:
                        stats['syslog'] = data
                        self.console.print("[green]Syslog retrieved successfully[/green]")
                    else:
                        self.console.print("[yellow]Syslog requires authentication[/yellow]")
                except:
                    self.console.print("[yellow]Syslog response is not JSON[/yellow]")
            
        except Exception as e:
            logger.error(f"Error getting network stats: {str(e)}")
        
        return stats
    
    def display_data(self, data: Dict[str, Any]):
        """Display extracted data in a nice format."""
        # System Information
        if data.get('system_info'):
            self.console.print("\n[bold]System Information:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in data['system_info'].items():
                table.add_row(key.title(), str(value))
            
            self.console.print(table)
        
        # CPU/Memory Information
        if data.get('cpu_memory'):
            self.console.print("\n[bold]CPU/Memory Information:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in data['cpu_memory'].items():
                table.add_row(key.title(), str(value))
            
            self.console.print(table)
        
        # Port Status
        if data.get('port_status'):
            self.console.print("\n[bold]Port Information:[/bold]")
            for i, port_data in enumerate(data['port_status']):
                self.console.print(f"\n[bold]Port Data Set {i+1}:[/bold]")
                table = Table(show_header=True, header_style="bold blue")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")
                
                for key, value in port_data.items():
                    table.add_row(key.title(), str(value))
                
                self.console.print(table)
        
        # VLAN Information
        if data.get('vlan_info'):
            self.console.print("\n[bold]VLAN Information:[/bold]")
            for i, vlan_data in enumerate(data['vlan_info']):
                if vlan_data.get('type') == 'vlan_config':
                    self.console.print(f"\n[bold]VLAN Configuration:[/bold]")
                    vlan_config = vlan_data.get('data', {})
                    
                    # Display VLAN list
                    if 'vlans' in vlan_config:
                        table = Table(show_header=True, header_style="bold blue")
                        table.add_column("VLAN ID", style="cyan")
                        table.add_column("VLAN Name", style="green")
                        
                        for vlan in vlan_config['vlans']:
                            table.add_row(str(vlan.get('val', '')), vlan.get('name', ''))
                        
                        self.console.print(table)
                    
                    # Display port VLAN assignments
                    if 'ports' in vlan_config:
                        self.console.print(f"\n[bold]Port VLAN Assignments:[/bold]")
                        port_table = Table(show_header=True, header_style="bold blue")
                        port_table.add_column("Port", style="cyan")
                        port_table.add_column("Mode", style="green")
                        port_table.add_column("Membership", style="yellow")
                        port_table.add_column("Forbidden", style="red")
                        port_table.add_column("PVID", style="blue")
                        
                        for i, port in enumerate(vlan_config['ports']):
                            port_table.add_row(
                                f"Port {i+1}",
                                str(port.get('mode', '')),
                                str(port.get('membership', '')),
                                str(port.get('forbidden', '')),
                                str(port.get('pvid', ''))
                            )
                        
                        self.console.print(port_table)
                
                elif vlan_data.get('type') == 'vlan_membership':
                    self.console.print(f"\n[bold]VLAN Membership Details:[/bold]")
                    membership_data = vlan_data.get('data', {})
                    
                    if 'ports' in membership_data:
                        membership_table = Table(show_header=True, header_style="bold blue")
                        membership_table.add_column("Port", style="cyan")
                        membership_table.add_column("Admin VLANs", style="green")
                        membership_table.add_column("Operational VLANs", style="yellow")
                        
                        for i, port in enumerate(membership_data['ports']):
                            membership_table.add_row(
                                f"Port {i+1}",
                                port.get('adminVlans', ''),
                                port.get('operVlans', '')
                            )
                        
                        self.console.print(membership_table)
        
        # MAC Address Table
        if data.get('mac_table'):
            self.console.print("\n[bold]MAC Address Table:[/bold]")
            for i, mac_data in enumerate(data['mac_table']):
                if mac_data.get('type') == 'dynamic_mac':
                    self.console.print(f"\n[bold]Dynamic MAC Addresses:[/bold]")
                    mac_info = mac_data.get('data', {})
                    
                    # Display aging time
                    if 'aging_time' in mac_info:
                        self.console.print(f"[cyan]Aging Time: {mac_info['aging_time']} seconds[/cyan]")
                    
                    # Display MAC entries
                    if 'entries' in mac_info:
                        self.console.print(f"[yellow]Resolving MAC vendors (this may take a moment due to rate limiting)...[/yellow]")
                        
                        table = Table(show_header=True, header_style="bold green")
                        table.add_column("VLAN", style="cyan")
                        table.add_column("MAC Address", style="green")
                        table.add_column("Port", style="yellow")
                        table.add_column("Vendor", style="magenta")
                        table.add_column("Key", style="blue")
                        
                        # Show progress for MAC lookups
                        total_entries = len(mac_info['entries'])
                        for i, entry in enumerate(mac_info['entries']):
                            mac_addr = entry.get('macAddr', '')
                            if mac_addr:
                                self.console.print(f"[cyan]Looking up vendor for {mac_addr} ({i+1}/{total_entries})...[/cyan]")
                                vendor = self._resolve_mac_vendor(mac_addr)
                            else:
                                vendor = "N/A"
                            
                            table.add_row(
                                str(entry.get('vlan', '')),
                                mac_addr,
                                entry.get('port', ''),
                                vendor,
                                entry.get('key', '')
                            )
                        
                        self.console.print(table)
                        
                        # Show cache statistics
                        cache_stats = self.get_mac_cache_stats()
                        self.console.print(f"[dim]MAC Cache: {cache_stats['cache_size']} entries cached, current delay: {cache_stats['current_delay']:.1f}s[/dim]")
                
                elif mac_data.get('type') == 'static_mac':
                    self.console.print(f"\n[bold]Static MAC Addresses:[/bold]")
                    mac_info = mac_data.get('data', {})
                    
                    if 'entries' in mac_info:
                        table = Table(show_header=True, header_style="bold blue")
                        table.add_column("VLAN", style="cyan")
                        table.add_column("MAC Address", style="green")
                        table.add_column("Port", style="yellow")
                        table.add_column("Vendor", style="magenta")
                        
                        for entry in mac_info['entries']:
                            if entry.get('macAddr'):  # Only show non-empty entries
                                mac_addr = entry.get('macAddr', '')
                                vendor = self._resolve_mac_vendor(mac_addr) if mac_addr else "N/A"
                                table.add_row(
                                    str(entry.get('vlan', '')),
                                    mac_addr,
                                    entry.get('port', ''),
                                    vendor
                                )
                        
                        if table.rows:
                            self.console.print(table)
                        else:
                            self.console.print("[yellow]No static MAC addresses configured[/yellow]")
                
                elif mac_data.get('type') == 'mac_status':
                    self.console.print(f"\n[bold]MAC Status Information:[/bold]")
                    mac_info = mac_data.get('data', {})
                    
                    if 'entries' in mac_info:
                        table = Table(show_header=True, header_style="bold magenta")
                        table.add_column("VLAN", style="cyan")
                        table.add_column("MAC Address", style="green")
                        table.add_column("Port", style="yellow")
                        table.add_column("Vendor", style="magenta")
                        table.add_column("Type", style="blue")
                        
                        for entry in mac_info['entries']:
                            mac_addr = entry.get('macAddr', '')
                            vendor = self._resolve_mac_vendor(mac_addr) if mac_addr else "N/A"
                            table.add_row(
                                str(entry.get('vlan', '')),
                                mac_addr,
                                entry.get('port', ''),
                                vendor,
                                entry.get('type', '')
                            )
                        
                        self.console.print(table)
        
        # Network Statistics
        if data.get('network_stats'):
            self.console.print("\n[bold]Network Statistics:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in data['network_stats'].items():
                table.add_row(key.title(), str(value))
            
            self.console.print(table)
    
    def export_data(self, filename: str = None) -> str:
        """Export data to JSON file."""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"final_switch_data_{timestamp}.json"
        
        data = self.get_comprehensive_data()
        filepath = f"/Users/jerome/ChineseSwitchParser/{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.console.print(f"[green]Data exported to: {filepath}[/green]")
            return filepath
            
        except Exception as e:
            self.console.print(f"[red]Export error: {str(e)}[/red]")
            logger.error(f"Export error: {str(e)}")
            return ""

@click.command()
@click.option('--url', default='http://10.41.8.33', help='Switch base URL')
@click.option('--username', help='Login username')
@click.option('--password', help='Login password')
@click.option('--export', help='Export data to JSON file')
@click.option('--mac-delay', default=1.0, help='Delay between MAC vendor lookups in seconds (default: 1.0)')
def main(url, username, password, export, mac_delay):
    """Final Chinese Switch Parser with real API access."""
    
    console = Console()
    console.print(Panel.fit(
        "[bold blue]Final Chinese Switch Parser[/bold blue]\n"
        "Accessing real API endpoints to extract switch data",
        border_style="blue"
    ))
    
    parser = FinalChineseSwitchParser(url, username, password)
    parser.mac_lookup_delay = mac_delay
    
    # Connect to switch
    if parser.connect():
        console.print("[green]Connected successfully![/green]")
        
        # Get comprehensive data
        console.print("\n[bold]Extracting switch data from API endpoints...[/bold]")
        data = parser.get_comprehensive_data()
        
        # Display data
        parser.display_data(data)
        
        # Export data if requested
        if export:
            parser.export_data(export)
        else:
            parser.export_data()
    else:
        console.print("[red]Failed to connect to switch[/red]")

if __name__ == "__main__":
    main()
