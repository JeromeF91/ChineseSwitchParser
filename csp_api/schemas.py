"""Normalized response schemas shared by all switch models.

These are the contract of the API: every supported model's quirks are
mapped INTO these shapes, so consumers never see per-vendor payload
dialects. Fields are Optional on purpose — embedded firmware is
inconsistent about what it exposes; absence means "this device does
not report it", never a parser bug.
"""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Services(BaseModel):
    """Management-plane service availability."""

    telnet: Optional[bool] = None
    ssh: Optional[bool] = None
    http: Optional[bool] = None
    https: Optional[bool] = None
    snmp: Optional[bool] = None


class SwitchInfo(BaseModel):
    hostname: Optional[str] = None
    sys_object_id: Optional[str] = None
    firmware_version: Optional[str] = None
    firmware_date: Optional[str] = None
    loader_version: Optional[str] = None
    base_mac: Optional[str] = None
    ipv4: Optional[str] = None
    ipv6: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    contact: Optional[str] = None
    system_time: Optional[str] = None
    uptime_seconds: Optional[int] = None
    cpu_pct: Optional[int] = None
    mem_pct: Optional[int] = None
    services: Optional[Services] = None


class SwitchCounters(BaseModel):
    """Switch-wide interface counters (the VM-S100 exposes totals, not
    per-port counters, via its port_count endpoint)."""

    in_octets: Optional[int] = None
    in_ucast_pkts: Optional[int] = None
    in_nucast_pkts: Optional[int] = None
    in_multicast_pkts: Optional[int] = None
    in_broadcast_pkts: Optional[int] = None
    in_discards: Optional[int] = None
    out_octets: Optional[int] = None
    out_ucast_pkts: Optional[int] = None
    out_nucast_pkts: Optional[int] = None
    out_multicast_pkts: Optional[int] = None
    out_broadcast_pkts: Optional[int] = None
    out_discards: Optional[int] = None


class Port(BaseModel):
    index: int
    name: Optional[str] = None
    present: bool = True
    """True when the device's panel layout reports this as a physical port."""
    link_up: Optional[bool] = None
    autonegotiate: Optional[bool] = None
    speed_mbps: Optional[int] = None
    duplex: Optional[str] = None  # "full" | "half" | None
    media: Optional[str] = None  # "fiber" | "copper" | None
    vlan_mode: Optional[str] = None  # "access" | "trunk" | "hybrid" | None
    pvid: Optional[int] = None
    uplink: Optional[bool] = None
    tagged: List[int] = Field(default_factory=list)
    untagged: List[int] = Field(default_factory=list)
    forbidden: List[int] = Field(default_factory=list)


class VlanMember(BaseModel):
    port_index: int
    port_name: Optional[str] = None
    tagged: bool = False


class Vlan(BaseModel):
    vlan_id: int
    name: Optional[str] = None
    members: List[VlanMember] = Field(default_factory=list)


class MacEntry(BaseModel):
    mac: str
    vlan_id: Optional[int] = None
    port: Optional[str] = None
    entry_type: Optional[str] = None  # "dynamic" | "static" | "management" | "cpu"


class LldpNeighbor(BaseModel):
    model_config = ConfigDict(extra="allow")

    local_port: Optional[str] = None
    chassis_id: Optional[str] = None
    system_name: Optional[str] = None
    port_id: Optional[str] = None


class SyslogEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    time: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None


class ResourceResponse(BaseModel):
    """Uniform envelope for every resource endpoint."""

    host: str
    url: str
    model: str
    fetched_at: str
    data: Any
    warnings: List[str] = Field(default_factory=list)


class HostSummary(BaseModel):
    name: str
    url: str
    model_configured: Optional[str] = None
