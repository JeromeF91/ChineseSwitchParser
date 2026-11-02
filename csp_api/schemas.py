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


# ---------------------------------------------------------------------------
# Extended resources (VIMIN fw 3.5.0.10 discovery, 2026-11-01)
# ---------------------------------------------------------------------------

class Route(BaseModel):
    dest: Optional[str] = None
    prefix_len: Optional[int] = None
    type: Optional[int] = None
    type_name: Optional[str] = None  # firmware codes: 0=default 1=dhcp 2=directly_connected 3=static
    next_hop: Optional[str] = None
    metric: Optional[int] = None
    admin_distance: Optional[int] = None
    interface: Optional[str] = None


class ArpEntry(BaseModel):
    ip: Optional[str] = None
    mac: Optional[str] = None
    vlan_id: Optional[int] = None
    interface: Optional[str] = None
    static: Optional[bool] = None


class MgmtIp(BaseModel):
    mode: Optional[str] = None  # "static" | "dhcp"
    ip: Optional[str] = None
    netmask: Optional[str] = None
    gateway: Optional[str] = None
    operating_gateway: Optional[str] = None
    ipv6: Optional[str] = None
    link_local: Optional[str] = None


class DnsInfo(BaseModel):
    enabled: Optional[bool] = None
    servers: List[str] = Field(default_factory=list)


class TimeInfo(BaseModel):
    sntp_enabled: Optional[bool] = None
    sntp_server: Optional[str] = None
    epoch: Optional[int] = None
    system_time: Optional[str] = None
    timezone_minutes: Optional[int] = None


class L3Snapshot(BaseModel):
    mgmt: Optional[MgmtIp] = None
    dns: Optional[DnsInfo] = None
    time: Optional[TimeInfo] = None
    interfaces: List[str] = Field(default_factory=list)
    routes: List[Route] = Field(default_factory=list)
    arp: List[ArpEntry] = Field(default_factory=list)
    arp_aging_seconds: Optional[int] = None


class StpGlobal(BaseModel):
    enabled: Optional[bool] = None
    mode: Optional[str] = None
    priority: Optional[int] = None
    hello_seconds: Optional[int] = None
    max_age_seconds: Optional[int] = None
    fwd_delay_seconds: Optional[int] = None
    tx_hold_count: Optional[int] = None
    region_name: Optional[str] = None
    revision: Optional[int] = None
    max_hop: Optional[int] = None
    bridge_id: Optional[str] = None
    root_bridge_id: Optional[str] = None
    root_cost: Optional[int] = None
    topology_change_count: Optional[int] = None


class StpPort(BaseModel):
    index: int
    name: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    path_cost: Optional[int] = None
    bpdu_guard: Optional[bool] = None
    bpdu_filter: Optional[bool] = None
    edge: Optional[bool] = None
    point_to_point: Optional[bool] = None
    role: Optional[str] = None    # e.g. "disabled", "designated", "root"
    state: Optional[str] = None   # e.g. "forwarding", "blocking", "learning"
    designated_bridge: Optional[str] = None
    designated_port: Optional[str] = None
    designated_cost: Optional[int] = None


class StpSnapshot(BaseModel):
    global_config: Optional[StpGlobal] = None
    ports: List[StpPort] = Field(default_factory=list)


class OpticsPort(BaseModel):
    index: int
    name: Optional[str] = None
    present: Optional[bool] = None       # from the optoelectronic-module label
    loss_of_signal: Optional[str] = None
    temperature_c: Optional[float] = None
    voltage_v: Optional[float] = None
    bias_ma: Optional[float] = None
    tx_power_mw: Optional[float] = None
    tx_power_dbm: Optional[float] = None
    rx_power_mw: Optional[float] = None
    rx_power_dbm: Optional[float] = None
    ddm_supported: bool = False


class MirrorSession(BaseModel):
    index: int
    enabled: Optional[bool] = None
    ingress_mirror: Optional[bool] = None
    source_rx: List[str] = Field(default_factory=list)
    source_tx: List[str] = Field(default_factory=list)
    destination: Optional[str] = None


class FirmwareStatus(BaseModel):
    dual_image_enabled: Optional[bool] = None
    active_index: Optional[int] = None
    selected_index: Optional[int] = None
    active_version: Optional[str] = None
    active_image: Optional[str] = None
    active_size_bytes: Optional[int] = None
    active_time: Optional[str] = None
    image_names: List[str] = Field(default_factory=list)


class UserAccount(BaseModel):
    username: str
    privilege: Optional[int] = None


class SnmpCommunity(BaseModel):
    """SENSITIVE: community strings are returned verbatim — treat this
    endpoint's output like credentials."""

    index: Optional[int] = None
    community: Optional[str] = None
    version_type: Optional[str] = None  # "basic" (v1/v2c) etc.
    access: Optional[str] = None        # "read_only" | "read_write"
    view: Optional[str] = None
