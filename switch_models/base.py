"""
Base switch model class for Chinese switch parsers.
This provides common functionality that all switch models can inherit from.
"""

import requests
import time
import re
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from rich.console import Console
import logging

logger = logging.getLogger(__name__)


class BaseSwitchModel(ABC):
    """Base class for all switch models."""
    
    def __init__(self, url: str, username: str, password: str, mac_lookup_delay: float = 1.0):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.console = Console()
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for embedded devices
        
        # MAC vendor lookup settings
        self.mac_vendor_cache = {}
        self.mac_lookup_lock = threading.Lock()
        self.last_mac_lookup_time = 0
        self.mac_lookup_delay = mac_lookup_delay
        
        # Model-specific configuration
        self.model_name = self.get_model_name()
        self.api_endpoints = self.get_api_endpoints()
        self.login_endpoint = self.get_login_endpoint()
        
    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name of this switch."""
        pass
    
    @abstractmethod
    def get_api_endpoints(self) -> Dict[str, str]:
        """Return the API endpoints specific to this model."""
        pass
    
    @abstractmethod
    def get_login_endpoint(self) -> str:
        """Return the login endpoint for this model."""
        pass
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the switch. Return True if successful."""
        pass
    
    def get_data(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get data from a specific API endpoint."""
        try:
            url = f"{self.url}/{endpoint}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError:
                    # If not JSON, return as text
                    return {"data": response.text}
            else:
                logger.warning(f"Failed to get data from {endpoint}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting data from {endpoint}: {str(e)}")
            return None
    
    def _resolve_mac_vendor(self, mac_address: str) -> str:
        """Resolve MAC address to vendor using MACVendors.com API with caching and rate limiting."""
        try:
            clean_mac = re.sub(r'[^0-9A-Fa-f]', '', mac_address.upper())
            oui = clean_mac[:6]
            
            if len(oui) != 6:
                return "Invalid MAC"
            
            with self.mac_lookup_lock:
                if oui in self.mac_vendor_cache:
                    return self.mac_vendor_cache[oui]
                
                current_time = time.time()
                time_since_last_lookup = current_time - self.last_mac_lookup_time
                
                if time_since_last_lookup < self.mac_lookup_delay:
                    sleep_time = self.mac_lookup_delay - time_since_last_lookup
                    time.sleep(sleep_time)
                
                self.last_mac_lookup_time = time.time()
            
            url = f"https://api.macvendors.com/{mac_address}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                vendor = response.text.strip()
                if vendor and not vendor.startswith("Not Found"):
                    with self.mac_lookup_lock:
                        self.mac_vendor_cache[oui] = vendor
                    return vendor
                else:
                    with self.mac_lookup_lock:
                        self.mac_vendor_cache[oui] = "Unknown Vendor"
                    return "Unknown Vendor"
            elif response.status_code == 404:
                # MAC address not found in database
                with self.mac_lookup_lock:
                    self.mac_vendor_cache[oui] = "Unregistered OUI"
                return "Unregistered OUI"
            elif response.status_code == 429:  # Rate limited
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
    
    def extract_all_data(self) -> Dict[str, Any]:
        """Extract all available data from the switch."""
        data = {
            "model": self.model_name,
            "url": self.url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data": {}
        }
        
        # Authenticate first
        if not self.authenticate():
            data["error"] = "Authentication failed"
            return data
        
        # Extract data from all endpoints
        for endpoint_name, endpoint_path in self.api_endpoints.items():
            self.console.print(f"Retrieving {endpoint_name}...")
            endpoint_data = self.get_data(endpoint_path)
            if endpoint_data:
                data["data"][endpoint_name] = endpoint_data
                self.console.print(f"[green]{endpoint_name} retrieved successfully[/green]")
            else:
                self.console.print(f"[red]Failed to retrieve {endpoint_name}[/red]")
        
        return data
    
    def display_data(self, data: Dict[str, Any]) -> None:
        """Display the extracted data in a formatted way."""
        self.console.print(f"\n[bold blue]Switch Model: {self.model_name}[/bold blue]")
        self.console.print(f"[bold blue]URL: {self.url}[/bold blue]")
        self.console.print(f"[bold blue]Timestamp: {data.get('timestamp', 'Unknown')}[/bold blue]\n")
        
        # Display each data section
        for section_name, section_data in data.get("data", {}).items():
            self.console.print(f"\n[bold yellow]{section_name.replace('_', ' ').title()}:[/bold yellow]")
            self.console.print(f"[dim]{section_data}[/dim]")
    
    def export_data(self, data: Dict[str, Any], filename: str) -> str:
        """Export data to a JSON file."""
        import json
        
        full_filename = f"{filename}_{self.model_name}_{time.strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(full_filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return full_filename
    
    def create_vlan(self, vlan_id: int, vlan_name: str) -> bool:
        """Create a VLAN. Override in model-specific implementations."""
        self.console.print(f"[yellow]VLAN creation not implemented for {self.model_name}[/yellow]")
        return False
    
    def delete_vlan(self, vlan_id: int) -> bool:
        """Delete a VLAN. Override in model-specific implementations."""
        self.console.print(f"[yellow]VLAN deletion not implemented for {self.model_name}[/yellow]")
        return False
    
    def enable_ssh(self) -> bool:
        """Enable SSH. Override in model-specific implementations."""
        self.console.print(f"[yellow]SSH enable not implemented for {self.model_name}[/yellow]")
        return False
    
    def disable_ssh(self) -> bool:
        """Disable SSH. Override in model-specific implementations."""
        self.console.print(f"[yellow]SSH disable not implemented for {self.model_name}[/yellow]")
        return False
