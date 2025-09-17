#!/usr/bin/env python3
"""
Chinese Switch Administrative Interface Parser

A sleek parser for Chinese network switch administrative interfaces.
Extracts configuration data, status information, and presents it in a clean format.
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
import click

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChineseSwitchParser:
    """Parser for Chinese switch administrative interfaces."""
    
    def __init__(self, base_url: str, username: str = None, password: str = None):
        """
        Initialize the parser with switch connection details.
        
        Args:
            base_url: Base URL of the switch (e.g., http://10.41.8.33)
            username: Login username (optional)
            password: Login password (optional)
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.console = Console()
        
        # Set up session headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.is_authenticated = False
        
    def connect(self) -> bool:
        """
        Connect to the switch and attempt authentication.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Connecting to switch...", total=None)
                
                # First, try to access the login page
                login_url = f"{self.base_url}/login.html"
                response = self.session.get(login_url, timeout=10)
                
                if response.status_code == 200:
                    progress.update(task, description="Login page accessed successfully")
                    time.sleep(1)
                    
                    # If credentials provided, attempt login
                    if self.username and self.password:
                        return self._authenticate(response.text)
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
    
    def _authenticate(self, login_page_html: str) -> bool:
        """
        Attempt to authenticate with the switch.
        
        Args:
            login_page_html: HTML content of the login page
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            soup = BeautifulSoup(login_page_html, 'html.parser')
            
            # Look for login form
            login_form = soup.find('form')
            if not login_form:
                self.console.print("[red]No login form found on the page[/red]")
                return False
            
            # Extract form action and method
            form_action = login_form.get('action', '')
            form_method = login_form.get('method', 'POST').upper()
            
            # Find input fields
            username_field = soup.find('input', {'name': ['username', 'user', 'login', 'account']})
            password_field = soup.find('input', {'type': 'password'})
            
            if not username_field or not password_field:
                self.console.print("[red]Could not find username/password fields[/red]")
                return False
            
            username_name = username_field.get('name')
            password_name = password_field.get('name')
            
            # Prepare login data
            login_data = {
                username_name: self.username,
                password_name: self.password
            }
            
            # Add any hidden fields
            for hidden_input in soup.find_all('input', {'type': 'hidden'}):
                name = hidden_input.get('name')
                value = hidden_input.get('value', '')
                if name:
                    login_data[name] = value
            
            # Submit login form
            login_url = urljoin(self.base_url, form_action)
            
            if form_method == 'POST':
                response = self.session.post(login_url, data=login_data, timeout=10)
            else:
                response = self.session.get(login_url, params=login_data, timeout=10)
            
            # Check if login was successful
            if response.status_code == 200:
                # Simple check: if we're redirected to a different page or get a success message
                if 'login' not in response.url.lower() or 'success' in response.text.lower():
                    self.is_authenticated = True
                    self.console.print("[green]Authentication successful![/green]")
                    return True
                else:
                    self.console.print("[red]Authentication failed. Check credentials.[/red]")
                    return False
            else:
                self.console.print(f"[red]Login request failed with status: {response.status_code}[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Authentication error: {str(e)}[/red]")
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Extract system information from the switch.
        
        Returns:
            Dict containing system information
        """
        if not self.is_authenticated:
            self.console.print("[red]Not authenticated. Please connect first.[/red]")
            return {}
        
        try:
            # Try common system info endpoints
            system_endpoints = [
                '/system.html',
                '/status.html',
                '/info.html',
                '/main.html',
                '/index.html'
            ]
            
            system_info = {}
            
            for endpoint in system_endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Extract system information from various common patterns
                        info = self._extract_system_data(soup)
                        if info:
                            system_info.update(info)
                            
                except Exception as e:
                    logger.debug(f"Failed to access {endpoint}: {str(e)}")
                    continue
            
            return system_info
            
        except Exception as e:
            self.console.print(f"[red]Error getting system info: {str(e)}[/red]")
            logger.error(f"Error getting system info: {str(e)}")
            return {}
    
    def _extract_system_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract system data from HTML soup.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Dict containing extracted system data
        """
        data = {}
        
        # Look for common system information patterns
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        data[key] = value
        
        # Look for specific system information in divs or spans
        info_selectors = [
            'div.system-info',
            'div.device-info',
            'span.device-name',
            'span.firmware-version',
            'span.model-number'
        ]
        
        for selector in info_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text:
                    data[selector.replace('div.', '').replace('span.', '')] = text
        
        return data
    
    def get_port_status(self) -> List[Dict[str, Any]]:
        """
        Extract port status information.
        
        Returns:
            List of dictionaries containing port information
        """
        if not self.is_authenticated:
            self.console.print("[red]Not authenticated. Please connect first.[/red]")
            return []
        
        try:
            # Try common port status endpoints
            port_endpoints = [
                '/port.html',
                '/ports.html',
                '/interface.html',
                '/status.html'
            ]
            
            ports = []
            
            for endpoint in port_endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        port_data = self._extract_port_data(soup)
                        if port_data:
                            ports.extend(port_data)
                            
                except Exception as e:
                    logger.debug(f"Failed to access {endpoint}: {str(e)}")
                    continue
            
            return ports
            
        except Exception as e:
            self.console.print(f"[red]Error getting port status: {str(e)}[/red]")
            logger.error(f"Error getting port status: {str(e)}")
            return []
    
    def _extract_port_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract port data from HTML soup.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of dictionaries containing port information
        """
        ports = []
        
        # Look for port tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            headers = []
            
            # Get headers from first row
            if rows:
                header_row = rows[0]
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
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
        
        return ports
    
    def display_system_info(self, system_info: Dict[str, Any]):
        """Display system information in a sleek format."""
        if not system_info:
            self.console.print("[yellow]No system information available[/yellow]")
            return
        
        table = Table(title="System Information", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        for key, value in system_info.items():
            table.add_row(key, str(value))
        
        self.console.print(table)
    
    def display_port_status(self, ports: List[Dict[str, Any]]):
        """Display port status in a sleek format."""
        if not ports:
            self.console.print("[yellow]No port information available[/yellow]")
            return
        
        table = Table(title="Port Status", show_header=True, header_style="bold magenta")
        
        # Add columns based on available data
        if ports:
            for key in ports[0].keys():
                table.add_column(key, style="cyan")
        
        for port in ports:
            row_data = [str(port.get(key, '')) for key in ports[0].keys()]
            table.add_row(*row_data)
        
        self.console.print(table)
    
    def export_data(self, filename: str = None) -> str:
        """
        Export all collected data to a JSON file.
        
        Args:
            filename: Output filename (optional)
            
        Returns:
            str: Path to the exported file
        """
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"switch_data_{timestamp}.json"
        
        data = {
            'system_info': self.get_system_info(),
            'port_status': self.get_port_status(),
            'exported_at': time.strftime("%Y-%m-%d %H:%M:%S"),
            'switch_url': self.base_url
        }
        
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
    """Chinese Switch Parser - Extract and display switch information."""
    
    console = Console()
    console.print(Panel.fit(
        "[bold blue]Chinese Switch Administrative Interface Parser[/bold blue]\n"
        "A sleek tool for extracting and displaying switch data",
        border_style="blue"
    ))
    
    # Initialize parser
    parser = ChineseSwitchParser(url, username, password)
    
    # Connect to switch
    if not parser.connect():
        console.print("[red]Failed to connect to switch. Exiting.[/red]")
        return
    
    # Get and display system information
    console.print("\n[bold]System Information:[/bold]")
    system_info = parser.get_system_info()
    parser.display_system_info(system_info)
    
    # Get and display port status
    console.print("\n[bold]Port Status:[/bold]")
    port_status = parser.get_port_status()
    parser.display_port_status(port_status)
    
    # Export data if requested
    if export:
        parser.export_data(export)
    elif not system_info and not port_status:
        # Auto-export if no data found but connection successful
        parser.export_data()

if __name__ == "__main__":
    main()

