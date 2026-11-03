"""Session pool over switch_models.

Embedded switch web UIs are slow and their sessions expire, so:
  - one switch_models instance per host, reused across requests;
  - authenticate() is called per snapshot (cheap single POST) and a
    failed fetch triggers exactly one re-auth + retry;
  - only the endpoints a resource actually needs are fetched — never
    the full extract_all_data() sweep.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional, Tuple

from switch_models import MODELS, detect_switch_model, get_model

from .registry import HostConfig

logger = logging.getLogger(__name__)

# resource -> endpoint keys (per canonical model). Endpoint keys are resolved
# against the live model instance's api_endpoints map, so a resource that an
# older firmware lacks simply produces a warning, not a crash.
RESOURCE_SECTIONS: Dict[str, Dict[str, List[str]]] = {
    "vm-s100-0800ms": {
        "info": ["system_info", "cpu_memory"],
        "ports": ["panel_info", "vlan_port", "vlan_membership", "port_bandwidth"],
        "vlans": ["vlan_config", "vlan_membership", "port_bandwidth"],
        "mac_table": ["mac_dynamic", "mac_static", "mac_status"],
        "lldp": ["lldp_neighbors"],
        "syslog": ["syslog"],
        "l3": ["mgmt_ip", "dns", "time", "l3_interfaces", "l3_routes", "l3_arp"],
        "stp": ["stp_global", "stp_ports", "port_bandwidth"],
        "optics": ["optical_ddm", "port_bandwidth"],
        "mirror": ["mirror_sessions"],
        "firmware": ["firmware_images", "firmware_img"],
        "users": ["local_users"],
        "snmp": ["snmp_communities"],
    },
}

RESOURCES = (
    "info", "ports", "vlans", "mac_table", "lldp", "syslog",
    "l3", "stp", "optics", "mirror", "firmware", "users", "snmp",
)


class SwitchUnavailable(RuntimeError):
    """Switch unreachable or authentication failed."""


class UnsupportedModel(RuntimeError):
    """Model has no normalizer yet (raw passthrough still available)."""

    def __init__(self, model_key: str, supported: List[str]):
        super().__init__(
            f"no normalizer for model {model_key!r}; "
            f"normalized endpoints support: {', '.join(supported)}"
        )
        self.model_key = model_key
        self.supported = supported


def canonical_model_key(client) -> str:
    """Canonical key for a model instance. Uses the model's own
    ``model_name`` (lowercased) — stable across firmware and consistent
    with the MODELS registry keys; aliases like 'vms1000800ms' never win.
    Falls back to the registry reverse-lookup only if model_name is unset."""
    name = getattr(client, "model_name", None)
    if isinstance(name, str) and name:
        return name.lower()
    cls = client if isinstance(client, type) else type(client)
    keys = [k for k, c in MODELS.items() if c is cls and k != "default"]
    return min(keys, key=lambda k: (len(k), k)) if keys else cls.__name__


class SwitchPool:
    def __init__(self) -> None:
        self._clients: Dict[str, Any] = {}
        self._detected: Dict[str, str] = {}
        self._lock = threading.Lock()

    # -- client management -------------------------------------------------

    def get_client(self, cfg: HostConfig):
        with self._lock:
            client = self._clients.get(cfg.name)
            if client is not None:
                return client

        if cfg.model:
            client = get_model(cfg.model)(cfg.url, cfg.username, cfg.password)  # type: ignore[call-abstract]  # get_model returns the class despite its annotation
        else:
            model_key = self._detected.get(cfg.name) or detect_switch_model(cfg.url)
            if not model_key:
                raise SwitchUnavailable(
                    f"could not reach or auto-detect switch at {cfg.url}"
                )
            client = get_model(model_key)(cfg.url, cfg.username, cfg.password)  # type: ignore[call-abstract]
            self._detected[cfg.name] = model_key

        with self._lock:
            self._clients[cfg.name] = client
        return client

    def model_key(self, cfg: HostConfig) -> str:
        return canonical_model_key(self.get_client(cfg))

    def reset(self, name: Optional[str] = None) -> None:
        with self._lock:
            if name is None:
                self._clients.clear()
                self._detected.clear()
            else:
                self._clients.pop(name, None)
                self._detected.pop(name, None)

    # -- data fetch ----------------------------------------------------------

    def fetch_raw(
        self, cfg: HostConfig, section_keys: List[str]
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Authenticate and fetch the given endpoint keys.

        Returns (sections, warnings). Raises SwitchUnavailable only if the
        device cannot be authenticated at all.
        """
        client = self.get_client(cfg)
        if not client.authenticate():
            raise SwitchUnavailable(
                f"authentication failed for {cfg.name} ({cfg.url})"
            )

        sections: Dict[str, Any] = {}
        warnings: List[str] = []
        for key in section_keys:
            endpoint = client.api_endpoints.get(key)
            if endpoint is None:
                # raw passthrough: any CGI command name the device supports
                # (see docs/VIMIN_COMMAND_REFERENCE.md), not just mapped keys
                endpoint = f"cgi/get.cgi?cmd={key}"
            data = client.get_data(endpoint)
            if data is None:
                # one re-auth + retry per section (session likely expired)
                if client.authenticate():
                    data = client.get_data(endpoint)
            if data is None:
                warnings.append(f"section {key!r} returned no data")
            else:
                sections[key] = data

        if not sections:
            raise SwitchUnavailable(
                f"no data retrieved from {cfg.name} ({cfg.url}) after re-auth"
            )
        return sections, warnings
