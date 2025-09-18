"""
Switch models package for Chinese switch parsers.
"""

import requests
from typing import List, Optional, Dict, Any
from .base import BaseSwitchModel
from .vm_s100_0800ms import VMS1000800MS
from .sl_swtg124as import SLSWTG124AS
from .sl_swtgw218as import SLSWTGW218AS
from .binardat_10g08_0800gsm import Binardat10G080800GSM

# Model registry
MODELS = {
    'vm-s100-0800ms': VMS1000800MS,
    'vms1000800ms': VMS1000800MS,
    'sl-swtg124as': SLSWTG124AS,
    'slswtg124as': SLSWTG124AS,
    'sl-swtgw218as': SLSWTGW218AS,
    'slswtgw218as': SLSWTGW218AS,
    '10g08-0800gsm': Binardat10G080800GSM,
    '10G08-0800GSM': Binardat10G080800GSM,
    'binardat-10g08-0800gsm': Binardat10G080800GSM,
    'binardat_10g08_0800gsm': Binardat10G080800GSM,
    'binardat': Binardat10G080800GSM,
    'default': VMS1000800MS
}

def get_model(model_name: str) -> BaseSwitchModel:
    """Get a switch model by name."""
    model_class = MODELS.get(model_name.lower())
    if not model_class:
        raise ValueError(f"Unknown model: {model_name}. Available models: {list(MODELS.keys())}")
    return model_class

def list_models() -> List[str]:
    """List all available models."""
    return list(MODELS.keys())

def detect_switch_model(url: str, timeout: int = 10) -> Optional[str]:
    """
    Automatically detect the switch model by analyzing the web interface.
    
    Args:
        url: Switch URL (e.g., http://10.41.8.33)
        timeout: Request timeout in seconds
        
    Returns:
        Detected model name or None if detection fails
    """
    try:
        # Clean up URL
        if not url.startswith(('http://', 'https://')):
            url = f"http://{url}"
        
        # Try to access the login page
        response = requests.get(f"{url}/login.html", timeout=timeout, verify=False, allow_redirects=True)
        
        if response.status_code == 200:
            content = response.text.lower()
            
            # Check for Binardat 10G08-0800GSM indicators
            if ('layer 3 switch' in content and 'iensuegdul27c90d' in content and 'rc4(' in content):
                return '10g08-0800gsm'
            
            # Check for VM-S100-0800MS indicators
            if any(indicator in content for indicator in [
                'vm-s100-0800ms',
                'vms1000800ms',
                'login.html?ver=',
                'home_loginAuth',
                'cgi/set.cgi',
                'login-box.css',
                'jquery.confirmon.css',
                'jquery.toastmessage.css',
                'ie=emulateie10'
            ]):
                return 'vm-s100-0800ms'
            
            # Check for SL-SWTGW218AS indicators
            if any(indicator in content for indicator in [
                'sl-swtgw218as',
                'slswtgw218as'
            ]):
                return 'sl-swtgw218as'
            
            # Check for SL-SWTG124AS indicators
            if any(indicator in content for indicator in [
                'sl-swtg124as',
                'slswtg124as',
                'md5.js',
                'vlan.cgi?page=static'
            ]):
                return 'sl-swtg124as'
        
        # Try alternative endpoints
        for endpoint in ['/login.cgi', '/cgi-bin/login', '/', '/index.cgi']:
            try:
                response = requests.get(f"{url}{endpoint}", timeout=timeout, verify=False, allow_redirects=True)
                if response.status_code == 200:
                    content = response.text.lower()
                    
                    # Check for Binardat 10G08-0800GSM indicators
                    if ('layer 3 switch' in content and 'iensuegdul27c90d' in content and 'rc4(' in content):
                        return '10g08-0800gsm'
                    
                    # Check for SL-SWTGW218AS indicators
                    if any(indicator in content for indicator in [
                        'sl-swtgw218as',
                        'slswtgw218as'
                    ]):
                        return 'sl-swtgw218as'
                    
                    # Check for SL-SWTG124AS indicators
                    if any(indicator in content for indicator in [
                        'sl-swtg124as',
                        'slswtg124as',
                        'md5.js',
                        'vlan.cgi?page=static'
                    ]):
                        return 'sl-swtg124as'
                    
                    # Check for VM-S100-0800MS indicators
                    if any(indicator in content for indicator in [
                        'vm-s100-0800ms',
                        'vms1000800ms',
                        'cgi/set.cgi',
                        'login-box.css',
                        'jquery.confirmon.css',
                        'jquery.toastmessage.css',
                        'ie=emulateie10'
                    ]):
                        return 'vm-s100-0800ms'
            except:
                continue
        
        return None
        
    except Exception as e:
        print(f"Error detecting switch model: {e}")
        return None

def get_model_with_detection(url: str, username: str, password: str, model_name: Optional[str] = None, mac_delay: float = 1.0) -> BaseSwitchModel:
    """
    Get a switch model instance with optional auto-detection.
    
    Args:
        url: Switch URL
        username: Username for authentication
        password: Password for authentication
        model_name: Specific model name (if None, will auto-detect)
        mac_delay: MAC vendor lookup delay
        
    Returns:
        Switch model instance
    """
    if model_name is None:
        print("Auto-detecting switch model...")
        detected_model = detect_switch_model(url)
        if detected_model:
            print(f"Detected switch model: {detected_model}")
            return get_model(detected_model)(url, username, password, mac_delay)
        else:
            print("Could not auto-detect switch model, using default (vm-s100-0800ms)")
            return get_model('default')(url, username, password, mac_delay)
    else:
        return get_model(model_name)(url, username, password, mac_delay)
