"""Server-side host registry.

Switch credentials never travel through the API — callers reference a
host by name, and the API resolves it here. Values may use an ``env:``
prefix (e.g. ``password: env:VIMIN33_PASSWORD``) so real secrets can
stay out of the YAML file entirely.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")

DEFAULT_HOSTS_FILE = "hosts.yaml"
HOSTS_FILE_ENV = "CSP_HOSTS_FILE"


class RegistryError(RuntimeError):
    pass


class HostConfig(BaseModel):
    name: str
    url: str
    username: str
    password: str
    model: Optional[str] = None
    """Canonical model key (see switch_models.MODELS). Omit to auto-detect
    on first use; set it explicitly when detection is ambiguous."""

    @field_validator("name")
    @classmethod
    def _valid_name(cls, v: str) -> str:
        if not _NAME_RE.match(v):
            raise ValueError(
                "host name must match ^[a-z0-9][a-z0-9-]{0,31}$ "
                "(e.g. 'vimin-33')"
            )
        return v

    @field_validator("url")
    @classmethod
    def _valid_url(cls, v: str) -> str:
        v = v.rstrip("/")
        if not v.startswith(("http://", "https://")):
            v = f"http://{v}"
        return v


def _resolve_env(value: str) -> str:
    if isinstance(value, str) and value.startswith("env:"):
        var = value[4:]
        resolved = os.environ.get(var)
        if resolved is None:
            raise RegistryError(f"environment variable {var!r} is not set")
        return resolved
    return value


def load_registry(path: Optional[Path] = None) -> Dict[str, HostConfig]:
    """Load and validate the host registry. Raises RegistryError on any
    problem — the API refuses to start with a broken registry."""
    if path is None:
        path = Path(os.environ.get(HOSTS_FILE_ENV, DEFAULT_HOSTS_FILE))
    if not path.exists():
        raise RegistryError(f"hosts file not found: {path}")

    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise RegistryError(f"invalid YAML in {path}: {exc}") from exc

    entries = doc.get("switches")
    if not isinstance(entries, list) or not entries:
        raise RegistryError(f"{path}: expected a non-empty 'switches:' list")

    hosts: Dict[str, HostConfig] = {}
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise RegistryError(f"{path}: switches[{i}] must be a mapping")
        try:
            cfg = HostConfig(
                name=entry.get("name", ""),
                url=entry.get("url", ""),
                username=_resolve_env(str(entry.get("username", ""))),
                password=_resolve_env(str(entry.get("password", ""))),
                model=entry.get("model"),
            )
        except ValueError as exc:
            raise RegistryError(f"{path}: switches[{i}]: {exc}") from exc
        if cfg.name in hosts:
            raise RegistryError(f"{path}: duplicate host name {cfg.name!r}")
        hosts[cfg.name] = cfg
    return hosts
