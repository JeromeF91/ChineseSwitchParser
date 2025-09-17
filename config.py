#!/usr/bin/env python3
"""
Configuration file for Chinese Switch Parser
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ParserConfig:
    """Configuration for the Chinese Switch Parser."""
    
    # Default switch settings
    default_url: str = "http://10.41.8.33"
    default_timeout: int = 10
    default_retry_attempts: int = 3
    
    # Web interface settings
    web_host: str = "0.0.0.0"
    web_port: int = 5000
    web_debug: bool = False
    
    # Data refresh settings
    auto_refresh_interval: int = 30  # seconds
    max_data_history: int = 100
    
    # Export settings
    default_export_format: str = "json"
    export_directory: str = "exports"
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Authentication settings
    auth_timeout: int = 15
    session_timeout: int = 3600  # 1 hour
    
    # Common switch endpoints to try
    common_endpoints: List[str] = None
    
    # HTML parsing settings
    max_table_rows: int = 1000
    max_table_columns: int = 20
    
    def __post_init__(self):
        """Initialize default values after object creation."""
        if self.common_endpoints is None:
            self.common_endpoints = [
                '/login.html',
                '/main.html',
                '/index.html',
                '/status.html',
                '/system.html',
                '/port.html',
                '/ports.html',
                '/interface.html',
                '/vlan.html',
                '/vlan_config.html',
                '/qos.html',
                '/security.html',
                '/statistics.html',
                '/device.html',
                '/info.html'
            ]
    
    @classmethod
    def from_env(cls) -> 'ParserConfig':
        """Create configuration from environment variables."""
        return cls(
            default_url=os.getenv('SWITCH_URL', 'http://10.41.8.33'),
            default_timeout=int(os.getenv('SWITCH_TIMEOUT', '10')),
            web_host=os.getenv('WEB_HOST', '0.0.0.0'),
            web_port=int(os.getenv('WEB_PORT', '5000')),
            web_debug=os.getenv('WEB_DEBUG', 'false').lower() == 'true',
            auto_refresh_interval=int(os.getenv('REFRESH_INTERVAL', '30')),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_file=os.getenv('LOG_FILE')
        )
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            'default_url': self.default_url,
            'default_timeout': self.default_timeout,
            'default_retry_attempts': self.default_retry_attempts,
            'web_host': self.web_host,
            'web_port': self.web_port,
            'web_debug': self.web_debug,
            'auto_refresh_interval': self.auto_refresh_interval,
            'max_data_history': self.max_data_history,
            'default_export_format': self.default_export_format,
            'export_directory': self.export_directory,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'auth_timeout': self.auth_timeout,
            'session_timeout': self.session_timeout,
            'common_endpoints': self.common_endpoints,
            'max_table_rows': self.max_table_rows,
            'max_table_columns': self.max_table_columns
        }

# Default configuration instance
DEFAULT_CONFIG = ParserConfig()

# Configuration for different switch types
SWITCH_CONFIGS = {
    'generic': ParserConfig(),
    'huawei': ParserConfig(
        common_endpoints=[
            '/login.html',
            '/main.html',
            '/system.html',
            '/port.html',
            '/vlan.html',
            '/qos.html'
        ]
    ),
    'zte': ParserConfig(
        common_endpoints=[
            '/login.html',
            '/main.html',
            '/system.html',
            '/port.html',
            '/vlan.html'
        ]
    ),
    'ruijie': ParserConfig(
        common_endpoints=[
            '/login.html',
            '/main.html',
            '/system.html',
            '/port.html',
            '/vlan.html'
        ]
    )
}

def get_config(switch_type: str = 'generic') -> ParserConfig:
    """Get configuration for specific switch type."""
    return SWITCH_CONFIGS.get(switch_type, DEFAULT_CONFIG)

