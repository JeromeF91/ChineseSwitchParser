"""
Configuration system for different switch models.
This allows easy addition of new models without code changes.
"""

import json
import os
from typing import Dict, Any


class ModelConfig:
    """Configuration manager for switch models."""
    
    def __init__(self, config_dir: str = "switch_models/configs"):
        self.config_dir = config_dir
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """Ensure the config directory exists."""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific model."""
        config_file = os.path.join(self.config_dir, f"{model_name.lower()}.json")
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            # Return default configuration
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "model_name": "Unknown",
            "api_endpoints": {},
            "login_endpoint": "cgi/login",
            "authentication_method": "form",
            "features": {
                "vlan_support": True,
                "mac_table_support": True,
                "port_statistics": True,
                "system_info": True
            }
        }
    
    def save_model_config(self, model_name: str, config: Dict[str, Any]):
        """Save configuration for a model."""
        config_file = os.path.join(self.config_dir, f"{model_name.lower()}.json")
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def list_available_configs(self) -> list:
        """List all available configuration files."""
        if not os.path.exists(self.config_dir):
            return []
        
        configs = []
        for file in os.listdir(self.config_dir):
            if file.endswith('.json'):
                configs.append(file[:-5])  # Remove .json extension
        
        return configs


# Predefined configurations for common models
VM_S100_0800MS_CONFIG = {
    "model_name": "VM-S100-0800MS",
    "api_endpoints": {
        "system_info": "cgi/get.cgi?cmd=sys_sysinfo",
        "cpu_memory": "cgi/get.cgi?cmd=sys_cpumem",
        "port_count": "cgi/get.cgi?cmd=port_cnt",
        "port_bandwidth": "cgi/get.cgi?cmd=port_bwutilz",
        "lag_info": "cgi/get.cgi?cmd=lag_mgmt",
        "syslog": "cgi/get.cgi?cmd=log_syslog",
        "panel_info": "cgi/get.cgi?cmd=panel_info",
        "panel_layout": "cgi/get.cgi?cmd=panel_layout",
        "vlan_config": "cgi/get.cgi?cmd=vlan_conf",
        "vlan_membership": "cgi/get.cgi?cmd=vlan_membership",
        "vlan_port": "cgi/get.cgi?cmd=vlan_port",
        "mac_dynamic": "cgi/get.cgi?cmd=mac_dynamic",
        "mac_static": "cgi/get.cgi?cmd=mac_static",
        "mac_status": "cgi/get.cgi?cmd=mac_miscStatus"
    },
    "login_endpoint": "cgi/home_loginAuth",
    "authentication_method": "form",
    "features": {
        "vlan_support": True,
        "mac_table_support": True,
        "port_statistics": True,
        "system_info": True,
        "vlan_management": True,
        "mac_vendor_lookup": True
    }
}

# Example configuration for a different model
EXAMPLE_OTHER_MODEL_CONFIG = {
    "model_name": "Example-Other-Model",
    "api_endpoints": {
        "system_info": "api/system",
        "port_info": "api/ports",
        "vlan_info": "api/vlans"
    },
    "login_endpoint": "api/login",
    "authentication_method": "json",
    "features": {
        "vlan_support": True,
        "mac_table_support": False,
        "port_statistics": True,
        "system_info": True
    }
}
