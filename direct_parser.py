#!/usr/bin/env python3
"""
Direct Chinese Switch Parser

A simplified parser that directly handles the specific switch authentication
and extracts real data using requests and BeautifulSoup.
"""

import requests
import json
import time
import re
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import click

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DirectChineseSwitchParser:
    """Direct parser for the specific Chinese switch."""
    
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
        self.login_data = {}
    
    def connect(self) -> bool:
        """Connect to the switch."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Connecting to switch...", total=None)
                
                # First, get the login page to extract any required data
                progress.update(task, description="Loading login page...")
                login_url = f"{self.base_url}/login.html"
                response = self.session.get(login_url, timeout=10)
                
                if response.status_code != 200:
                    self.console.print(f"[red]Failed to access login page. Status: {response.status_code}[/red]")
                    return False
                
                progress.update(task, description="Analyzing login page...")
                
                # Parse the login page
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract any required data from the page
                self._extract_login_data(soup)
                
                # If credentials provided, try to authenticate
                if self.username and self.password:
                    progress.update(task, description="Attempting authentication...")
                    return self._authenticate(soup)
                else:
                    self.console.print("[yellow]No credentials provided. Trying to access without authentication...[/yellow]")
                    return self._try_access_without_auth()
                    
        except Exception as e:
            self.console.print(f"[red]Connection error: {str(e)}[/red]")
            logger.error(f"Connection error: {str(e)}")
            return False
    
    def _extract_login_data(self, soup: BeautifulSoup):
        """Extract any required data from the login page."""
        try:
            # Look for any JavaScript variables or hidden fields that might be needed
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for common patterns
                    if 'modulus' in script.string:
                        # Extract RSA modulus if present
                        modulus_match = re.search(r'modulus["\']?\s*:\s*["\']([^"\']+)["\']', script.string)
                        if modulus_match:
                            self.login_data['modulus'] = modulus_match.group(1)
                    
                    if 'exponent' in script.string:
                        # Extract RSA exponent if present
                        exp_match = re.search(r'exponent["\']?\s*:\s*["\']([^"\']+)["\']', script.string)
                        if exp_match:
                            self.login_data['exponent'] = exp_match.group(1)
            
            # Look for hidden form fields
            hidden_inputs = soup.find_all('input', {'type': 'hidden'})
            for input_field in hidden_inputs:
                name = input_field.get('name')
                value = input_field.get('value', '')
                if name:
                    self.login_data[name] = value
            
        except Exception as e:
            logger.error(f"Error extracting login data: {str(e)}")
    
    def _authenticate(self, soup: BeautifulSoup) -> bool:
        """Authenticate with the switch."""
        try:
            # Find the form
            form = soup.find('form', {'id': 'setform'})
            if not form:
                # Try alternative selectors
                form = soup.find('form')
                if form:
                    self.console.print(f"[yellow]Found form with id: {form.get('id', 'no-id')}[/yellow]")
                else:
                    self.console.print("[red]Could not find any login form[/red]")
                    # Debug: show all forms found
                    forms = soup.find_all('form')
                    self.console.print(f"[yellow]Found {len(forms)} forms on page[/yellow]")
                    for i, f in enumerate(forms):
                        self.console.print(f"  Form {i+1}: id='{f.get('id', 'no-id')}', action='{f.get('action', 'no-action')}'")
                    return False
            
            # Prepare login data
            login_data = {
                'username': self.username,
                'password': self.password,
                'save_name': 'on',  # Checkbox for saving username
                'save_pass': 'on',  # Checkbox for saving password
                **self.login_data  # Include any extracted data
            }
            
            # Try to submit the form
            # First, let's try a POST request to the login endpoint
            login_endpoints = [
                '/login.html',
                '/login.cgi',
                '/auth.cgi',
                '/login.php',
                '/cgi-bin/login'
            ]
            
            for endpoint in login_endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    
                    # Try POST first
                    response = self.session.post(url, data=login_data, timeout=10)
                    
                    if response.status_code == 200:
                        # Check if we're redirected away from login page
                        if 'login' not in response.url.lower() or 'success' in response.text.lower():
                            self.is_authenticated = True
                            self.console.print("[green]Authentication successful![/green]")
                            return True
                        
                        # Check if there's a success message in the response
                        if any(keyword in response.text.lower() for keyword in ['success', 'welcome', 'main', 'dashboard']):
                            self.is_authenticated = True
                            self.console.print("[green]Authentication successful![/green]")
                            return True
                
                except Exception as e:
                    logger.debug(f"Failed to authenticate via {endpoint}: {str(e)}")
                    continue
            
            # If POST didn't work, try GET with parameters
            for endpoint in login_endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = self.session.get(url, params=login_data, timeout=10)
                    
                    if response.status_code == 200 and 'login' not in response.url.lower():
                        self.is_authenticated = True
                        self.console.print("[green]Authentication successful![/green]")
                        return True
                
                except Exception as e:
                    logger.debug(f"Failed to authenticate via GET {endpoint}: {str(e)}")
                    continue
            
            self.console.print("[red]Authentication failed with all methods[/red]")
            return False
            
        except Exception as e:
            self.console.print(f"[red]Authentication error: {str(e)}[/red]")
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def _try_access_without_auth(self) -> bool:
        """Try to access switch data without authentication."""
        try:
            # Try common pages that might be accessible
            common_pages = [
                '/main.html',
                '/index.html',
                '/status.html',
                '/system.html',
                '/port.html',
                '/info.html'
            ]
            
            for page in common_pages:
                try:
                    url = f"{self.base_url}{page}"
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200 and 'login' not in response.url.lower():
                        self.is_authenticated = True
                        self.console.print(f"[green]Access successful via {page}[/green]")
                        return True
                except:
                    continue
            
            # If no specific pages work, try to extract data from the login page itself
            login_url = f"{self.base_url}/login.html"
            response = self.session.get(login_url, timeout=10)
            
            if response.status_code == 200:
                # Check if there's any useful data in the login page
                soup = BeautifulSoup(response.text, 'html.parser')
                page_text = soup.get_text().lower()
                
                if any(keyword in page_text for keyword in ['system', 'port', 'vlan', 'status', 'device']):
                    self.is_authenticated = True
                    self.console.print("[green]Found data on login page[/green]")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error trying access without auth: {str(e)}")
            return False
    
    def get_comprehensive_data(self) -> Dict[str, Any]:
        """Get comprehensive switch data."""
        if not self.is_authenticated:
            self.console.print("[red]Not authenticated. Please connect first.[/red]")
            return {}
        
        data = {
            'system_info': self._extract_system_info(),
            'port_status': self._extract_port_status(),
            'vlan_info': self._extract_vlan_info(),
            'device_info': self._extract_device_info(),
            'raw_data': self._extract_raw_data(),
            'exported_at': time.strftime("%Y-%m-%d %H:%M:%S"),
            'switch_url': self.base_url
        }
        
        return data
    
    def _extract_system_info(self) -> Dict[str, Any]:
        """Extract system information."""
        system_info = {}
        
        try:
            # Try multiple endpoints for system information
            system_endpoints = [
                '/main.html',
                '/index.html',
                '/status.html',
                '/system.html',
                '/info.html',
                '/login.html'  # Sometimes info is on login page
            ]
            
            for endpoint in system_endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        info = self._parse_system_info(soup)
                        if info:
                            system_info.update(info)
                            
                except Exception as e:
                    logger.debug(f"Failed to get system info from {endpoint}: {str(e)}")
                    continue
            
            if system_info:
                self.console.print(f"[green]Extracted system info: {len(system_info)} fields[/green]")
            else:
                self.console.print("[yellow]No system information found[/yellow]")
                
        except Exception as e:
            logger.error(f"Error extracting system info: {str(e)}")
        
        return system_info
    
    def _parse_system_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse system information from HTML."""
        info = {}
        
        try:
            # Look for tables with system information
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        
                        # Map common system info keys
                        if any(term in key for term in ['model', '型号', 'device']):
                            info['model'] = value
                        elif any(term in key for term in ['version', '版本', 'firmware']):
                            info['version'] = value
                        elif any(term in key for term in ['uptime', '运行时间', '运行']):
                            info['uptime'] = value
                        elif any(term in key for term in ['ip', '地址', 'address']):
                            info['ip_address'] = value
                        elif any(term in key for term in ['mac', 'mac address']):
                            info['mac_address'] = value
                        elif any(term in key for term in ['gateway', '网关']):
                            info['gateway'] = value
                        elif any(term in key for term in ['subnet', 'mask', '子网']):
                            info['subnet_mask'] = value
            
            # Look for JavaScript variables that might contain system info
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for common patterns
                    patterns = {
                        'model': [r'model["\']?\s*[:=]\s*["\']([^"\']+)["\']', r'型号["\']?\s*[:=]\s*["\']([^"\']+)["\']'],
                        'version': [r'version["\']?\s*[:=]\s*["\']([^"\']+)["\']', r'版本["\']?\s*[:=]\s*["\']([^"\']+)["\']'],
                        'ip': [r'ip["\']?\s*[:=]\s*["\']([0-9.]+)["\']', r'地址["\']?\s*[:=]\s*["\']([0-9.]+)["\']'],
                        'mac': [r'mac["\']?\s*[:=]\s*["\']([0-9a-fA-F:]{17})["\']']
                    }
                    
                    for key, pattern_list in patterns.items():
                        for pattern in pattern_list:
                            matches = re.findall(pattern, script.string, re.IGNORECASE)
                            if matches and key not in info:
                                info[key] = matches[0].strip()
            
            # Look for any text content that might contain system info
            page_text = soup.get_text()
            
            # IP address pattern
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            ip_matches = re.findall(ip_pattern, page_text)
            if ip_matches and 'ip_address' not in info:
                info['ip_address'] = ip_matches[0]
            
            # MAC address pattern
            mac_pattern = r'\b(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}\b'
            mac_matches = re.findall(mac_pattern, page_text)
            if mac_matches and 'mac_address' not in info:
                info['mac_address'] = mac_matches[0]
        
        except Exception as e:
            logger.error(f"Error parsing system info: {str(e)}")
        
        return info
    
    def _extract_port_status(self) -> List[Dict[str, Any]]:
        """Extract port status information."""
        ports = []
        
        try:
            # Try multiple endpoints for port information
            port_endpoints = [
                '/port.html',
                '/ports.html',
                '/interface.html',
                '/status.html',
                '/main.html'
            ]
            
            for endpoint in port_endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        port_data = self._parse_port_info(soup)
                        if port_data:
                            ports.extend(port_data)
                            
                except Exception as e:
                    logger.debug(f"Failed to get port info from {endpoint}: {str(e)}")
                    continue
            
            if ports:
                self.console.print(f"[green]Extracted {len(ports)} ports[/green]")
            else:
                self.console.print("[yellow]No port information found[/yellow]")
                
        except Exception as e:
            logger.error(f"Error extracting port status: {str(e)}")
        
        return ports
    
    def _parse_port_info(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse port information from HTML."""
        ports = []
        
        try:
            # Look for tables that might contain port information
            tables = soup.find_all('table')
            
            for table in tables:
                table_text = table.get_text().lower()
                
                # Check if this table might contain port information
                if any(term in table_text for term in ['port', '端口', 'interface', '接口', 'ethernet', '以太网']):
                    rows = table.find_all('tr')
                    if not rows:
                        continue
                    
                    # Get headers
                    headers = []
                    header_row = rows[0]
                    header_cells = header_row.find_all(['th', 'td'])
                    
                    for cell in header_cells:
                        headers.append(cell.get_text(strip=True).lower())
                    
                    # Process data rows
                    for row in rows[1:]:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            port_data = {}
                            for i, cell in enumerate(cells):
                                if i < len(headers):
                                    port_data[headers[i]] = cell.get_text(strip=True)
                            
                            if port_data:
                                ports.append(port_data)
        
        except Exception as e:
            logger.error(f"Error parsing port info: {str(e)}")
        
        return ports
    
    def _extract_vlan_info(self) -> List[Dict[str, Any]]:
        """Extract VLAN information."""
        vlans = []
        
        try:
            # Try VLAN-specific endpoints
            vlan_endpoints = [
                '/vlan.html',
                '/vlan_config.html',
                '/vlan_setting.html',
                '/main.html'
            ]
            
            for endpoint in vlan_endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        vlan_data = self._parse_vlan_info(soup)
                        if vlan_data:
                            vlans.extend(vlan_data)
                            
                except Exception as e:
                    logger.debug(f"Failed to get VLAN info from {endpoint}: {str(e)}")
                    continue
            
            if vlans:
                self.console.print(f"[green]Extracted {len(vlans)} VLANs[/green]")
            else:
                self.console.print("[yellow]No VLAN information found[/yellow]")
                
        except Exception as e:
            logger.error(f"Error extracting VLAN info: {str(e)}")
        
        return vlans
    
    def _parse_vlan_info(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse VLAN information from HTML."""
        vlans = []
        
        try:
            tables = soup.find_all('table')
            
            for table in tables:
                table_text = table.get_text().lower()
                
                if any(term in table_text for term in ['vlan', '虚拟局域网', '网段']):
                    rows = table.find_all('tr')
                    if not rows:
                        continue
                    
                    headers = []
                    header_row = rows[0]
                    header_cells = header_row.find_all(['th', 'td'])
                    
                    for cell in header_cells:
                        headers.append(cell.get_text(strip=True).lower())
                    
                    for row in rows[1:]:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            vlan_data = {}
                            for i, cell in enumerate(cells):
                                if i < len(headers):
                                    vlan_data[headers[i]] = cell.get_text(strip=True)
                            
                            if vlan_data:
                                vlans.append(vlan_data)
        
        except Exception as e:
            logger.error(f"Error parsing VLAN info: {str(e)}")
        
        return vlans
    
    def _extract_device_info(self) -> Dict[str, Any]:
        """Extract device information."""
        device_info = {}
        
        try:
            # Get basic page information
            login_url = f"{self.base_url}/login.html"
            response = self.session.get(login_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Get page title
                title = soup.find('title')
                if title:
                    device_info['title'] = title.get_text(strip=True)
                
                # Look for any device-related information in the page
                page_text = soup.get_text()
                
                # Extract any useful information
                device_info['page_size'] = len(response.text)
                device_info['has_javascript'] = len(soup.find_all('script')) > 0
                device_info['has_forms'] = len(soup.find_all('form')) > 0
                device_info['has_tables'] = len(soup.find_all('table')) > 0
                
                # Look for any version or model information in the text
                version_patterns = [
                    r'version[:\s]*([0-9.]+)',
                    r'版本[:\s]*([0-9.]+)',
                    r'v([0-9.]+)',
                    r'ver[:\s]*([0-9.]+)'
                ]
                
                for pattern in version_patterns:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    if matches:
                        device_info['detected_version'] = matches[0]
                        break
        
        except Exception as e:
            logger.error(f"Error extracting device info: {str(e)}")
        
        return device_info
    
    def _extract_raw_data(self) -> Dict[str, Any]:
        """Extract raw data from the switch."""
        raw_data = {}
        
        try:
            # Get the main page content
            login_url = f"{self.base_url}/login.html"
            response = self.session.get(login_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract all text content
                raw_data['page_text'] = soup.get_text()
                
                # Extract all links
                links = soup.find_all('a', href=True)
                raw_data['links'] = [{'text': link.get_text(strip=True), 'href': link['href']} for link in links]
                
                # Extract all forms
                forms = soup.find_all('form')
                raw_data['forms'] = []
                for form in forms:
                    form_data = {
                        'action': form.get('action', ''),
                        'method': form.get('method', 'GET'),
                        'inputs': []
                    }
                    
                    inputs = form.find_all('input')
                    for input_field in inputs:
                        input_data = {
                            'name': input_field.get('name', ''),
                            'type': input_field.get('type', 'text'),
                            'value': input_field.get('value', ''),
                            'id': input_field.get('id', '')
                        }
                        form_data['inputs'].append(input_data)
                    
                    raw_data['forms'].append(form_data)
                
                # Extract all tables
                tables = soup.find_all('table')
                raw_data['tables'] = []
                for table in tables:
                    table_data = {
                        'rows': []
                    }
                    
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        row_data = [cell.get_text(strip=True) for cell in cells]
                        table_data['rows'].append(row_data)
                    
                    raw_data['tables'].append(table_data)
        
        except Exception as e:
            logger.error(f"Error extracting raw data: {str(e)}")
        
        return raw_data
    
    def display_data(self, data: Dict[str, Any]):
        """Display extracted data."""
        # System Information
        if data.get('system_info'):
            self.console.print("\n[bold]System Information:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in data['system_info'].items():
                table.add_row(key.title(), str(value))
            
            self.console.print(table)
        
        # Port Status
        if data.get('port_status'):
            self.console.print("\n[bold]Port Status:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            
            if data['port_status']:
                for key in data['port_status'][0].keys():
                    table.add_column(key.title(), style="cyan")
                
                for port in data['port_status']:
                    row_data = [str(port.get(key, '')) for key in data['port_status'][0].keys()]
                    table.add_row(*row_data)
            
            self.console.print(table)
        
        # VLAN Information
        if data.get('vlan_info'):
            self.console.print("\n[bold]VLAN Information:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            
            if data['vlan_info']:
                for key in data['vlan_info'][0].keys():
                    table.add_column(key.title(), style="cyan")
                
                for vlan in data['vlan_info']:
                    row_data = [str(vlan.get(key, '')) for key in data['vlan_info'][0].keys()]
                    table.add_row(*row_data)
            
            self.console.print(table)
        
        # Device Information
        if data.get('device_info'):
            self.console.print("\n[bold]Device Information:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in data['device_info'].items():
                table.add_row(key.title(), str(value))
            
            self.console.print(table)
        
        # Raw Data Summary
        if data.get('raw_data'):
            raw_data = data['raw_data']
            self.console.print("\n[bold]Raw Data Summary:[/bold]")
            self.console.print(f"  • Page text length: {len(raw_data.get('page_text', ''))}")
            self.console.print(f"  • Links found: {len(raw_data.get('links', []))}")
            self.console.print(f"  • Forms found: {len(raw_data.get('forms', []))}")
            self.console.print(f"  • Tables found: {len(raw_data.get('tables', []))}")
    
    def export_data(self, filename: str = None) -> str:
        """Export data to JSON file."""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"direct_switch_data_{timestamp}.json"
        
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
def main(url, username, password, export):
    """Direct Chinese Switch Parser with real data extraction."""
    
    console = Console()
    console.print(Panel.fit(
        "[bold blue]Direct Chinese Switch Parser[/bold blue]\n"
        "Extracting real data from the switch interface",
        border_style="blue"
    ))
    
    parser = DirectChineseSwitchParser(url, username, password)
    
    # Connect to switch
    if parser.connect():
        console.print("[green]Connected successfully![/green]")
        
        # Get comprehensive data
        console.print("\n[bold]Extracting switch data...[/bold]")
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
