"""
Switch models package for Chinese switch parsers.
"""

from typing import List
from .base import BaseSwitchModel
from .vm_s100_0800ms import VMS1000800MS
from .sl_swtg124as import SLSWTG124AS

# Model registry
MODELS = {
    'vm-s100-0800ms': VMS1000800MS,
    'vms1000800ms': VMS1000800MS,
    'sl-swtg124as': SLSWTG124AS,
    'slswtg124as': SLSWTG124AS,
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
