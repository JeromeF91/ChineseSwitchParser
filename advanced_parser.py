#!/usr/bin/env python3
"""
Advanced Chinese Switch Parser with Enhanced Data Extraction

This module provides advanced parsing capabilities for Chinese network switches,
including VLAN configuration, QoS settings, and real-time monitoring.
"""

import requests
import json
import time
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich import print as rprint
import click
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SwitchPort:
    """Data class for switch port information."""
    port_id: str
    status: str
    speed: str
    duplex: str
    vlan: str
    description: str
    mac_address: str = ""
    rx_bytes: int = 0
    tx_bytes: int = 0
    rx_packets: int = 0
    tx_packets: int = 0

@dataclass
class VLANInfo:
    """Data class for VLAN information."""
    vlan_id: str
    name: str
    status: str
    ports: List[str]
    description: str = ""

@dataclass
class SystemInfo:
    """Data class for system information."""
    model: str
    firmware_version: str
    uptime: str
    mac_address: str
    ip_address: str
    subnet_mask: str
    gateway: str
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    temperature: float = 0.0

class AdvancedChineseSwitchParser:
    """Advanced parser for Chinese switch administrative interfaces."""
    
    def __init__(self, base_url: str, username: str = None, password: str = None):
        """Initialize the advanced parser."""
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.console = Console()
        
        # Enhanced headers for better compatibility
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        self.is_authenticated = False
        self.discovered_endpoints = set()
        self.switch_type = "unknown"
        
    def connect(self) -> bool:
        """Connect to the switch with enhanced discovery."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Connecting to switch...", total=None)
                
                # Try to access the main page first
                main_url = f"{self.base_url}/"
                response = self.session.get(main_url, timeout=15)
                
                if response.status_code == 200:
                    progress.update(task, description="Main page accessed")
                    
                    # Discover available endpoints
                    self._discover_endpoints(response.text)
                    
                    # Try authentication if credentials provided
                    if self.username and self.password:
                        progress.update(task, description="Attempting authentication...")
                        return self._authenticate_advanced()
                    else:
                        self.console.print("[yellow]No credentials provided. Accessing in read-only mode.[/yellow]")
                        self.is_authenticated = True
                        return True
                else:
                    self.console.print(f"[red]Failed to connect to switch. Status code: {response.status_code}[/red]")
                    return False
                    
        except requests.exceptions.RequestException as e:
            self.console.print(f"[red]Connection error: {str(e)}[/red]")
            logger.error(f"Connection error: {str(e)}")
            return False
    
    def _discover_endpoints(self, html_content: str):
        """Discover available endpoints from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all links
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            if href.startswith('/') or href.startswith('./'):
                self.discovered_endpoints.add(href)
        
        # Find all form actions
        forms = soup.find_all('form', action=True)
        for form in forms:
            action = form['action']
            if action.startswith('/') or action.startswith('./'):
                self.discovered_endpoints.add(action)
        
        # Look for JavaScript AJAX calls
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Find common AJAX patterns
                ajax_patterns = [
                    r'["\']([^"\']*\.html[^"\']*)["\']',
                    r'["\']([^"\']*\.cgi[^"\']*)["\']',
                    r'["\']([^"\']*\.php[^"\']*)["\']'
                ]
                for pattern in ajax_patterns:
                    matches = re.findall(pattern, script.string)
                    for match in matches:
                        if match.startswith('/') or match.startswith('./'):
                            self.discovered_endpoints.add(match)
        
        logger.info(f"Discovered {len(self.discovered_endpoints)} endpoints")
    
    def _authenticate_advanced(self) -> bool:
        """Advanced authentication with multiple strategies."""
        auth_strategies = [
            self._try_standard_login,
            self._try_ajax_login,
            self._try_form_login,
            self._try_cookie_auth
        ]
        
        for strategy in auth_strategies:
            try:
                if strategy():
                    self.is_authenticated = True
                    self.console.print("[green]Authentication successful![/green]")
                    return True
            except Exception as e:
                logger.debug(f"Auth strategy failed: {str(e)}")
                continue
        
        self.console.print("[red]All authentication strategies failed[/red]")
        return False
    
    def _try_standard_login(self) -> bool:
        """Try standard form-based login."""
        login_url = f"{self.base_url}/login.html"
        response = self.session.get(login_url, timeout=10)
        
        if response.status_code != 200:
            return False
        
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form')
        
        if not form:
            return False
        
        # Extract form data
        form_data = {}
        for input_tag in form.find_all('input'):
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            input_type = input_tag.get('type', 'text')
            
            if name:
                if input_type == 'password' and self.password:
                    form_data[name] = self.password
                elif input_type == 'text' and self.username:
                    form_data[name] = self.username
                else:
                    form_data[name] = value
        
        # Submit form
        action = form.get('action', '')
        if action.startswith('/'):
            action = f"{self.base_url}{action}"
        elif not action.startswith('http'):
            action = urljoin(login_url, action)
        
        method = form.get('method', 'POST').upper()
        
        if method == 'POST':
            response = self.session.post(action, data=form_data, timeout=10)
        else:
            response = self.session.get(action, params=form_data, timeout=10)
        
        # Check for successful login indicators
        success_indicators = [
            'main.html', 'index.html', 'status.html',
            'dashboard', 'welcome', 'success'
        ]
        
        for indicator in success_indicators:
            if indicator in response.url.lower() or indicator in response.text.lower():
                return True
        
        return False
    
    def _try_ajax_login(self) -> bool:
        """Try AJAX-based login."""
        # Look for AJAX login endpoints
        ajax_endpoints = [
            '/login.cgi',
            '/auth.cgi',
            '/login.php',
            '/api/login'
        ]
        
        for endpoint in ajax_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                data = {
                    'username': self.username,
                    'password': self.password,
                    'action': 'login'
                }
                
                response = self.session.post(url, data=data, timeout=10)
                
                if response.status_code == 200:
                    try:
                        json_response = response.json()
                        if json_response.get('success') or json_response.get('status') == 'ok':
                            return True
                    except:
                        if 'success' in response.text.lower():
                            return True
            except:
                continue
        
        return False
    
    def _try_form_login(self) -> bool:
        """Try alternative form login methods."""
        # Try different login page variations
        login_pages = [
            '/login.html',
            '/login.htm',
            '/user_login.html',
            '/admin_login.html',
            '/index.html'
        ]
        
        for page in login_pages:
            try:
                url = f"{self.base_url}{page}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for login forms with different patterns
                    forms = soup.find_all('form')
                    for form in forms:
                        if self._submit_form(form, url):
                            return True
            except:
                continue
        
        return False
    
    def _try_cookie_auth(self) -> bool:
        """Try cookie-based authentication."""
        # Some switches use cookie-based auth
        try:
            # Try to access a protected page
            protected_pages = [
                '/status.html',
                '/port.html',
                '/vlan.html',
                '/system.html'
            ]
            
            for page in protected_pages:
                url = f"{self.base_url}{page}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200 and 'login' not in response.url.lower():
                    return True
        except:
            pass
        
        return False
    
    def _submit_form(self, form, base_url: str) -> bool:
        """Submit a form and check for success."""
        try:
            form_data = {}
            for input_tag in form.find_all('input'):
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                input_type = input_tag.get('type', 'text')
                
                if name:
                    if input_type == 'password' and self.password:
                        form_data[name] = self.password
                    elif input_type == 'text' and self.username:
                        form_data[name] = self.username
                    else:
                        form_data[name] = value
            
            action = form.get('action', '')
            if action.startswith('/'):
                action = f"{self.base_url}{action}"
            elif not action.startswith('http'):
                action = urljoin(base_url, action)
            
            method = form.get('method', 'POST').upper()
            
            if method == 'POST':
                response = self.session.post(action, data=form_data, timeout=10)
            else:
                response = self.session.get(action, params=form_data, timeout=10)
            
            # Check for success
            success_indicators = [
                'main.html', 'index.html', 'status.html',
                'dashboard', 'welcome', 'success'
            ]
            
            for indicator in success_indicators:
                if indicator in response.url.lower() or indicator in response.text.lower():
                    return True
            
            return False
        except:
            return False
    
    def get_comprehensive_data(self) -> Dict[str, Any]:
        """Get comprehensive switch data."""
        if not self.is_authenticated:
            self.console.print("[red]Not authenticated. Please connect first.[/red]")
            return {}
        
        data = {
            'system_info': self.get_system_info_advanced(),
            'port_status': self.get_port_status_advanced(),
            'vlan_info': self.get_vlan_info(),
            'qos_settings': self.get_qos_settings(),
            'security_settings': self.get_security_settings(),
            'statistics': self.get_statistics(),
            'exported_at': datetime.now().isoformat(),
            'switch_url': self.base_url
        }
        
        return data
    
    def get_system_info_advanced(self) -> SystemInfo:
        """Get advanced system information."""
        system_info = SystemInfo(
            model="Unknown",
            firmware_version="Unknown",
            uptime="Unknown",
            mac_address="Unknown",
            ip_address="Unknown",
            subnet_mask="Unknown",
            gateway="Unknown"
        )
        
        # Try multiple endpoints for system info
        system_endpoints = [
            '/system.html', '/status.html', '/info.html',
            '/main.html', '/index.html', '/device.html'
        ]
        
        for endpoint in system_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    info = self._extract_system_info_advanced(soup)
                    if info:
                        system_info = info
                        break
            except Exception as e:
                logger.debug(f"Failed to get system info from {endpoint}: {str(e)}")
                continue
        
        return system_info
    
    def _extract_system_info_advanced(self, soup: BeautifulSoup) -> Optional[SystemInfo]:
        """Extract advanced system information from HTML."""
        try:
            # Look for system information in tables
            tables = soup.find_all('table')
            system_data = {}
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        
                        # Map common system info keys
                        if 'model' in key or '设备型号' in key:
                            system_data['model'] = value
                        elif 'firmware' in key or 'version' in key or '版本' in key:
                            system_data['firmware_version'] = value
                        elif 'uptime' in key or '运行时间' in key:
                            system_data['uptime'] = value
                        elif 'mac' in key and 'address' in key:
                            system_data['mac_address'] = value
                        elif 'ip' in key and 'address' in key:
                            system_data['ip_address'] = value
                        elif 'subnet' in key or 'mask' in key:
                            system_data['subnet_mask'] = value
                        elif 'gateway' in key or '网关' in key:
                            system_data['gateway'] = value
                        elif 'cpu' in key and 'usage' in key:
                            try:
                                system_data['cpu_usage'] = float(re.findall(r'[\d.]+', value)[0])
                            except:
                                pass
                        elif 'memory' in key and 'usage' in key:
                            try:
                                system_data['memory_usage'] = float(re.findall(r'[\d.]+', value)[0])
                            except:
                                pass
                        elif 'temperature' in key or '温度' in key:
                            try:
                                system_data['temperature'] = float(re.findall(r'[\d.]+', value)[0])
                            except:
                                pass
            
            # Create SystemInfo object
            return SystemInfo(
                model=system_data.get('model', 'Unknown'),
                firmware_version=system_data.get('firmware_version', 'Unknown'),
                uptime=system_data.get('uptime', 'Unknown'),
                mac_address=system_data.get('mac_address', 'Unknown'),
                ip_address=system_data.get('ip_address', 'Unknown'),
                subnet_mask=system_data.get('subnet_mask', 'Unknown'),
                gateway=system_data.get('gateway', 'Unknown'),
                cpu_usage=system_data.get('cpu_usage', 0.0),
                memory_usage=system_data.get('memory_usage', 0.0),
                temperature=system_data.get('temperature', 0.0)
            )
            
        except Exception as e:
            logger.error(f"Error extracting system info: {str(e)}")
            return None
    
    def get_port_status_advanced(self) -> List[SwitchPort]:
        """Get advanced port status information."""
        ports = []
        
        # Try multiple endpoints for port information
        port_endpoints = [
            '/port.html', '/ports.html', '/interface.html',
            '/status.html', '/port_status.html'
        ]
        
        for endpoint in port_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    port_data = self._extract_port_info_advanced(soup)
                    if port_data:
                        ports.extend(port_data)
                        break
            except Exception as e:
                logger.debug(f"Failed to get port info from {endpoint}: {str(e)}")
                continue
        
        return ports
    
    def _extract_port_info_advanced(self, soup: BeautifulSoup) -> List[SwitchPort]:
        """Extract advanced port information from HTML."""
        ports = []
        
        try:
            # Look for port tables
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                if not rows:
                    continue
                
                # Get headers
                headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(['th', 'td'])]
                
                # Process data rows
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue
                    
                    port_data = {}
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            port_data[headers[i]] = cell.get_text(strip=True)
                    
                    # Create SwitchPort object
                    if port_data:
                        port = SwitchPort(
                            port_id=port_data.get('port', port_data.get('interface', 'Unknown')),
                            status=port_data.get('status', port_data.get('state', 'Unknown')),
                            speed=port_data.get('speed', port_data.get('速率', 'Unknown')),
                            duplex=port_data.get('duplex', port_data.get('双工', 'Unknown')),
                            vlan=port_data.get('vlan', port_data.get('vlan id', 'Unknown')),
                            description=port_data.get('description', port_data.get('描述', '')),
                            mac_address=port_data.get('mac', port_data.get('mac address', '')),
                            rx_bytes=int(port_data.get('rx bytes', port_data.get('接收字节', '0'))),
                            tx_bytes=int(port_data.get('tx bytes', port_data.get('发送字节', '0'))),
                            rx_packets=int(port_data.get('rx packets', port_data.get('接收包', '0'))),
                            tx_packets=int(port_data.get('tx packets', port_data.get('发送包', '0')))
                        )
                        ports.append(port)
            
        except Exception as e:
            logger.error(f"Error extracting port info: {str(e)}")
        
        return ports
    
    def get_vlan_info(self) -> List[VLANInfo]:
        """Get VLAN information."""
        vlans = []
        
        # Try VLAN-specific endpoints
        vlan_endpoints = [
            '/vlan.html', '/vlan_config.html', '/vlan_setting.html'
        ]
        
        for endpoint in vlan_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    vlan_data = self._extract_vlan_info(soup)
                    if vlan_data:
                        vlans.extend(vlan_data)
                        break
            except Exception as e:
                logger.debug(f"Failed to get VLAN info from {endpoint}: {str(e)}")
                continue
        
        return vlans
    
    def _extract_vlan_info(self, soup: BeautifulSoup) -> List[VLANInfo]:
        """Extract VLAN information from HTML."""
        vlans = []
        
        try:
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                if not rows:
                    continue
                
                headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(['th', 'td'])]
                
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue
                    
                    vlan_data = {}
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            vlan_data[headers[i]] = cell.get_text(strip=True)
                    
                    if vlan_data:
                        vlan = VLANInfo(
                            vlan_id=vlan_data.get('vlan id', vlan_data.get('id', 'Unknown')),
                            name=vlan_data.get('name', vlan_data.get('vlan name', 'Unknown')),
                            status=vlan_data.get('status', vlan_data.get('state', 'Unknown')),
                            ports=vlan_data.get('ports', vlan_data.get('成员端口', '').split(',') if vlan_data.get('成员端口') else []),
                            description=vlan_data.get('description', vlan_data.get('描述', ''))
                        )
                        vlans.append(vlan)
        
        except Exception as e:
            logger.error(f"Error extracting VLAN info: {str(e)}")
        
        return vlans
    
    def get_qos_settings(self) -> Dict[str, Any]:
        """Get QoS settings."""
        # Placeholder for QoS settings extraction
        return {"qos_enabled": False, "policies": []}
    
    def get_security_settings(self) -> Dict[str, Any]:
        """Get security settings."""
        # Placeholder for security settings extraction
        return {"mac_filtering": False, "port_security": False}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get switch statistics."""
        # Placeholder for statistics extraction
        return {"total_ports": 0, "active_ports": 0, "total_vlans": 0}
    
    def display_comprehensive_data(self, data: Dict[str, Any]):
        """Display comprehensive switch data in a sleek format."""
        # System Information
        if data.get('system_info'):
            self._display_system_info_advanced(data['system_info'])
        
        # Port Status
        if data.get('port_status'):
            self._display_port_status_advanced(data['port_status'])
        
        # VLAN Information
        if data.get('vlan_info'):
            self._display_vlan_info(data['vlan_info'])
    
    def _display_system_info_advanced(self, system_info: SystemInfo):
        """Display advanced system information."""
        table = Table(title="System Information", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row("Model", system_info.model)
        table.add_row("Firmware Version", system_info.firmware_version)
        table.add_row("Uptime", system_info.uptime)
        table.add_row("MAC Address", system_info.mac_address)
        table.add_row("IP Address", system_info.ip_address)
        table.add_row("Subnet Mask", system_info.subnet_mask)
        table.add_row("Gateway", system_info.gateway)
        
        if system_info.cpu_usage > 0:
            table.add_row("CPU Usage", f"{system_info.cpu_usage}%")
        if system_info.memory_usage > 0:
            table.add_row("Memory Usage", f"{system_info.memory_usage}%")
        if system_info.temperature > 0:
            table.add_row("Temperature", f"{system_info.temperature}°C")
        
        self.console.print(table)
    
    def _display_port_status_advanced(self, ports: List[SwitchPort]):
        """Display advanced port status."""
        if not ports:
            self.console.print("[yellow]No port information available[/yellow]")
            return
        
        table = Table(title="Port Status", show_header=True, header_style="bold magenta")
        table.add_column("Port", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Speed", style="blue")
        table.add_column("Duplex", style="blue")
        table.add_column("VLAN", style="yellow")
        table.add_column("Description", style="white")
        
        for port in ports:
            status_color = "green" if port.status.lower() in ['up', 'active', '启用'] else "red"
            table.add_row(
                port.port_id,
                f"[{status_color}]{port.status}[/{status_color}]",
                port.speed,
                port.duplex,
                port.vlan,
                port.description
            )
        
        self.console.print(table)
    
    def _display_vlan_info(self, vlans: List[VLANInfo]):
        """Display VLAN information."""
        if not vlans:
            self.console.print("[yellow]No VLAN information available[/yellow]")
            return
        
        table = Table(title="VLAN Information", show_header=True, header_style="bold magenta")
        table.add_column("VLAN ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="blue")
        table.add_column("Ports", style="yellow")
        table.add_column("Description", style="white")
        
        for vlan in vlans:
            status_color = "green" if vlan.status.lower() in ['active', 'up', '启用'] else "red"
            ports_str = ', '.join(vlan.ports) if vlan.ports else 'None'
            
            table.add_row(
                vlan.vlan_id,
                vlan.name,
                f"[{status_color}]{vlan.status}[/{status_color}]",
                ports_str,
                vlan.description
            )
        
        self.console.print(table)
    
    def export_data(self, filename: str = None) -> str:
        """Export comprehensive data to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"switch_data_advanced_{timestamp}.json"
        
        data = self.get_comprehensive_data()
        
        # Convert dataclasses to dictionaries
        if data.get('system_info'):
            data['system_info'] = data['system_info'].__dict__
        
        if data.get('port_status'):
            data['port_status'] = [port.__dict__ for port in data['port_status']]
        
        if data.get('vlan_info'):
            data['vlan_info'] = [vlan.__dict__ for vlan in data['vlan_info']]
        
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
def main(url, username, password, export):
    """Advanced Chinese Switch Parser - Extract and display comprehensive switch information."""
    
    console = Console()
    console.print(Panel.fit(
        "[bold blue]Advanced Chinese Switch Parser[/bold blue]\n"
        "Comprehensive switch data extraction and analysis",
        border_style="blue"
    ))
    
    # Initialize parser
    parser = AdvancedChineseSwitchParser(url, username, password)
    
    # Connect to switch
    if not parser.connect():
        console.print("[red]Failed to connect to switch. Exiting.[/red]")
        return
    
    # Get comprehensive data
    console.print("\n[bold]Gathering comprehensive switch data...[/bold]")
    data = parser.get_comprehensive_data()
    
    # Display data
    parser.display_comprehensive_data(data)
    
    # Export data if requested
    if export:
        parser.export_data(export)
    else:
        # Auto-export with timestamp
        parser.export_data()

if __name__ == "__main__":
    main()

