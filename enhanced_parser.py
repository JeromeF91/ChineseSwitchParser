#!/usr/bin/env python3
"""
Enhanced Chinese Switch Parser with Real Data Extraction

This parser uses Selenium to handle JavaScript-based authentication
and extract real data from the switch interface.
"""

import time
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import click

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SwitchData:
    """Data class for extracted switch information."""
    system_info: Dict[str, Any]
    port_status: List[Dict[str, Any]]
    vlan_info: List[Dict[str, Any]]
    interface_stats: List[Dict[str, Any]]
    device_info: Dict[str, Any]

class EnhancedChineseSwitchParser:
    """Enhanced parser using Selenium for JavaScript-based switches."""
    
    def __init__(self, base_url: str, username: str = None, password: str = None):
        """Initialize the enhanced parser."""
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.console = Console()
        self.driver = None
        self.is_authenticated = False
        
    def _setup_driver(self):
        """Setup Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            return True
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            return False
    
    def connect(self) -> bool:
        """Connect to the switch using Selenium."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Setting up browser...", total=None)
                
                if not self._setup_driver():
                    self.console.print("[red]Failed to setup browser driver[/red]")
                    return False
                
                progress.update(task, description="Navigating to switch...")
                
                # Navigate to the switch
                self.driver.get(f"{self.base_url}/login.html")
                time.sleep(3)
                
                progress.update(task, description="Analyzing login page...")
                
                # Check if we're on the login page
                if "login" in self.driver.current_url.lower():
                    if self.username and self.password:
                        progress.update(task, description="Attempting login...")
                        return self._authenticate()
                    else:
                        self.console.print("[yellow]No credentials provided. Trying to access without authentication...[/yellow]")
                        return self._try_access_without_auth()
                else:
                    self.console.print("[green]Already authenticated or no login required[/green]")
                    self.is_authenticated = True
                    return True
                    
        except Exception as e:
            self.console.print(f"[red]Connection error: {str(e)}[/red]")
            logger.error(f"Connection error: {str(e)}")
            return False
    
    def _authenticate(self) -> bool:
        """Authenticate with the switch."""
        try:
            # Look for username field
            username_selectors = [
                "input[name='username']",
                "input[name='user']",
                "input[name='login']",
                "input[name='account']",
                "input[type='text']",
                "#username",
                "#user",
                "#login"
            ]
            
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not username_field:
                self.console.print("[red]Could not find username field[/red]")
                return False
            
            # Look for password field
            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "input[name='pass']",
                "#password",
                "#pass"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                self.console.print("[red]Could not find password field[/red]")
                return False
            
            # Enter credentials
            username_field.clear()
            username_field.send_keys(self.username)
            
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Look for login button
            login_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "input[value*='login']",
                "input[value*='Login']",
                "button:contains('Login')",
                "button:contains('login')",
                ".login-btn",
                "#login-btn",
                "#login"
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if login_button:
                login_button.click()
            else:
                # Try pressing Enter on password field
                password_field.send_keys("\n")
            
            # Wait for page to load
            time.sleep(5)
            
            # Check if login was successful
            if "login" not in self.driver.current_url.lower():
                self.is_authenticated = True
                self.console.print("[green]Authentication successful![/green]")
                return True
            else:
                self.console.print("[red]Authentication failed[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Authentication error: {str(e)}[/red]")
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def _try_access_without_auth(self) -> bool:
        """Try to access switch data without authentication."""
        try:
            # Try to navigate to common pages
            common_pages = [
                "/main.html",
                "/index.html", 
                "/status.html",
                "/system.html",
                "/port.html"
            ]
            
            for page in common_pages:
                try:
                    self.driver.get(f"{self.base_url}{page}")
                    time.sleep(2)
                    
                    if "login" not in self.driver.current_url.lower():
                        self.is_authenticated = True
                        self.console.print(f"[green]Access successful via {page}[/green]")
                        return True
                except:
                    continue
            
            # If we're still on login page, try to find any accessible content
            if "login" in self.driver.current_url.lower():
                # Look for any data in the login page itself
                page_source = self.driver.page_source
                if any(keyword in page_source.lower() for keyword in ['system', 'port', 'vlan', 'status']):
                    self.is_authenticated = True
                    self.console.print("[green]Found data on login page[/green]")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error trying access without auth: {str(e)}")
            return False
    
    def get_comprehensive_data(self) -> SwitchData:
        """Get comprehensive switch data."""
        if not self.is_authenticated:
            self.console.print("[red]Not authenticated. Please connect first.[/red]")
            return SwitchData({}, [], [], [], {})
        
        try:
            system_info = self._extract_system_info()
            port_status = self._extract_port_status()
            vlan_info = self._extract_vlan_info()
            interface_stats = self._extract_interface_stats()
            device_info = self._extract_device_info()
            
            return SwitchData(
                system_info=system_info,
                port_status=port_status,
                vlan_info=vlan_info,
                interface_stats=interface_stats,
                device_info=device_info
            )
            
        except Exception as e:
            self.console.print(f"[red]Error getting comprehensive data: {str(e)}[/red]")
            logger.error(f"Error getting comprehensive data: {str(e)}")
            return SwitchData({}, [], [], [], {})
    
    def _extract_system_info(self) -> Dict[str, Any]:
        """Extract system information."""
        system_info = {}
        
        try:
            # Get page source
            page_source = self.driver.page_source
            
            # Look for system information in various formats
            import re
            
            # Common patterns for system info
            patterns = {
                'model': [r'model[:\s]*([^\n\r<]+)', r'型号[:\s]*([^\n\r<]+)', r'device[:\s]*([^\n\r<]+)'],
                'version': [r'version[:\s]*([^\n\r<]+)', r'版本[:\s]*([^\n\r<]+)', r'firmware[:\s]*([^\n\r<]+)'],
                'uptime': [r'uptime[:\s]*([^\n\r<]+)', r'运行时间[:\s]*([^\n\r<]+)', r'运行[:\s]*([^\n\r<]+)'],
                'ip': [r'ip[:\s]*([0-9.]+)', r'地址[:\s]*([0-9.]+)', r'([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})'],
                'mac': [r'mac[:\s]*([0-9a-fA-F:]{17})', r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})']
            }
            
            for key, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    if matches:
                        system_info[key] = matches[0].strip()
                        break
            
            # Try to find tables with system information
            try:
                tables = self.driver.find_elements(By.TAG_NAME, "table")
                for table in tables:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 2:
                            key = cells[0].text.strip().lower()
                            value = cells[1].text.strip()
                            
                            if any(term in key for term in ['model', '型号', 'device']):
                                system_info['model'] = value
                            elif any(term in key for term in ['version', '版本', 'firmware']):
                                system_info['version'] = value
                            elif any(term in key for term in ['uptime', '运行时间', '运行']):
                                system_info['uptime'] = value
                            elif any(term in key for term in ['ip', '地址']):
                                system_info['ip'] = value
                            elif any(term in key for term in ['mac']):
                                system_info['mac'] = value
            except:
                pass
            
            # If we found any system info, mark as successful
            if system_info:
                self.console.print(f"[green]Extracted system info: {len(system_info)} fields[/green]")
            else:
                self.console.print("[yellow]No system information found[/yellow]")
            
        except Exception as e:
            logger.error(f"Error extracting system info: {str(e)}")
        
        return system_info
    
    def _extract_port_status(self) -> List[Dict[str, Any]]:
        """Extract port status information."""
        ports = []
        
        try:
            # Look for port-related tables or elements
            port_selectors = [
                "table[id*='port']",
                "table[class*='port']",
                ".port-table",
                "#port-table",
                "table:contains('Port')",
                "table:contains('端口')"
            ]
            
            for selector in port_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        ports.extend(self._parse_port_table(element))
                except:
                    continue
            
            # If no specific port tables found, look for any tables that might contain port data
            if not ports:
                tables = self.driver.find_elements(By.TAG_NAME, "table")
                for table in tables:
                    table_text = table.text.lower()
                    if any(term in table_text for term in ['port', '端口', 'interface', '接口']):
                        ports.extend(self._parse_port_table(table))
            
            if ports:
                self.console.print(f"[green]Extracted {len(ports)} ports[/green]")
            else:
                self.console.print("[yellow]No port information found[/yellow]")
                
        except Exception as e:
            logger.error(f"Error extracting port status: {str(e)}")
        
        return ports
    
    def _parse_port_table(self, table_element) -> List[Dict[str, Any]]:
        """Parse a table element for port information."""
        ports = []
        
        try:
            rows = table_element.find_elements(By.TAG_NAME, "tr")
            if not rows:
                return ports
            
            # Get headers
            headers = []
            header_row = rows[0]
            header_cells = header_row.find_elements(By.TAG_NAME, "th")
            if not header_cells:
                header_cells = header_row.find_elements(By.TAG_NAME, "td")
            
            for cell in header_cells:
                headers.append(cell.text.strip().lower())
            
            # Process data rows
            for row in rows[1:]:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 2:
                    port_data = {}
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            port_data[headers[i]] = cell.text.strip()
                    
                    if port_data:
                        ports.append(port_data)
        
        except Exception as e:
            logger.error(f"Error parsing port table: {str(e)}")
        
        return ports
    
    def _extract_vlan_info(self) -> List[Dict[str, Any]]:
        """Extract VLAN information."""
        vlans = []
        
        try:
            # Look for VLAN-related content
            vlan_selectors = [
                "table[id*='vlan']",
                "table[class*='vlan']",
                ".vlan-table",
                "#vlan-table"
            ]
            
            for selector in vlan_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        vlans.extend(self._parse_vlan_table(element))
                except:
                    continue
            
            if vlans:
                self.console.print(f"[green]Extracted {len(vlans)} VLANs[/green]")
            else:
                self.console.print("[yellow]No VLAN information found[/yellow]")
                
        except Exception as e:
            logger.error(f"Error extracting VLAN info: {str(e)}")
        
        return vlans
    
    def _parse_vlan_table(self, table_element) -> List[Dict[str, Any]]:
        """Parse a table element for VLAN information."""
        vlans = []
        
        try:
            rows = table_element.find_elements(By.TAG_NAME, "tr")
            if not rows:
                return vlans
            
            # Get headers
            headers = []
            header_row = rows[0]
            header_cells = header_row.find_elements(By.TAG_NAME, "th")
            if not header_cells:
                header_cells = header_row.find_elements(By.TAG_NAME, "td")
            
            for cell in header_cells:
                headers.append(cell.text.strip().lower())
            
            # Process data rows
            for row in rows[1:]:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 2:
                    vlan_data = {}
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            vlan_data[headers[i]] = cell.text.strip()
                    
                    if vlan_data:
                        vlans.append(vlan_data)
        
        except Exception as e:
            logger.error(f"Error parsing VLAN table: {str(e)}")
        
        return vlans
    
    def _extract_interface_stats(self) -> List[Dict[str, Any]]:
        """Extract interface statistics."""
        # Placeholder for interface statistics
        return []
    
    def _extract_device_info(self) -> Dict[str, Any]:
        """Extract device information."""
        device_info = {}
        
        try:
            # Get page title and basic info
            device_info['title'] = self.driver.title
            device_info['url'] = self.driver.current_url
            
            # Look for any device-related information
            page_source = self.driver.page_source
            
            # Extract any JavaScript variables that might contain device info
            import re
            js_vars = re.findall(r'var\s+(\w+)\s*=\s*["\']([^"\']+)["\']', page_source)
            for var_name, var_value in js_vars:
                if any(term in var_name.lower() for term in ['device', 'model', 'version', 'info']):
                    device_info[var_name] = var_value
        
        except Exception as e:
            logger.error(f"Error extracting device info: {str(e)}")
        
        return device_info
    
    def display_data(self, data: SwitchData):
        """Display extracted data in a nice format."""
        # System Information
        if data.system_info:
            self.console.print("\n[bold]System Information:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in data.system_info.items():
                table.add_row(key.title(), str(value))
            
            self.console.print(table)
        
        # Port Status
        if data.port_status:
            self.console.print("\n[bold]Port Status:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            
            if data.port_status:
                # Add columns based on available data
                for key in data.port_status[0].keys():
                    table.add_column(key.title(), style="cyan")
                
                for port in data.port_status:
                    row_data = [str(port.get(key, '')) for key in data.port_status[0].keys()]
                    table.add_row(*row_data)
            
            self.console.print(table)
        
        # VLAN Information
        if data.vlan_info:
            self.console.print("\n[bold]VLAN Information:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            
            if data.vlan_info:
                for key in data.vlan_info[0].keys():
                    table.add_column(key.title(), style="cyan")
                
                for vlan in data.vlan_info:
                    row_data = [str(vlan.get(key, '')) for key in data.vlan_info[0].keys()]
                    table.add_row(*row_data)
            
            self.console.print(table)
        
        # Device Information
        if data.device_info:
            self.console.print("\n[bold]Device Information:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in data.device_info.items():
                table.add_row(key.title(), str(value))
            
            self.console.print(table)
    
    def export_data(self, filename: str = None) -> str:
        """Export data to JSON file."""
        if not filename:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_switch_data_{timestamp}.json"
        
        data = self.get_comprehensive_data()
        
        # Convert dataclass to dictionary
        export_data = {
            'system_info': data.system_info,
            'port_status': data.port_status,
            'vlan_info': data.vlan_info,
            'interface_stats': data.interface_stats,
            'device_info': data.device_info,
            'exported_at': datetime.datetime.now().isoformat(),
            'switch_url': self.base_url
        }
        
        filepath = f"/Users/jerome/ChineseSwitchParser/{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.console.print(f"[green]Data exported to: {filepath}[/green]")
            return filepath
            
        except Exception as e:
            self.console.print(f"[red]Export error: {str(e)}[/red]")
            logger.error(f"Export error: {str(e)}")
            return ""
    
    def close(self):
        """Close the browser driver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

@click.command()
@click.option('--url', default='http://10.41.8.33', help='Switch base URL')
@click.option('--username', help='Login username')
@click.option('--password', help='Login password')
@click.option('--export', help='Export data to JSON file')
def main(url, username, password, export):
    """Enhanced Chinese Switch Parser with real data extraction."""
    
    console = Console()
    console.print(Panel.fit(
        "[bold blue]Enhanced Chinese Switch Parser[/bold blue]\n"
        "Using Selenium for JavaScript-based authentication and data extraction",
        border_style="blue"
    ))
    
    parser = EnhancedChineseSwitchParser(url, username, password)
    
    try:
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
    
    finally:
        parser.close()

if __name__ == "__main__":
    main()
