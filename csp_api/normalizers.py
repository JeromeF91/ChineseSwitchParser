"""Per-model normalizers: raw vendor payloads -> csp_api.schemas.

Each supported model registers a set of functions keyed by resource.
Everything defensive by design: these firmware builds return i18n
template strings (``lang('sys','txtSysUptimeArg',[0,13,27,55])``),
placeholder rows (empty MAC entries), and section shapes that vary by
firmware version. A field we can't parse cleanly comes back as None,
never as a guess.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from .schemas import (
    ArpEntry,
    DnsInfo,
    FirmwareStatus,
    L3Snapshot,
    LldpNeighbor,
    MacEntry,
    MgmtIp,
    MirrorSession,
    OpticsPort,
    Port,
    Route,
    Services,
    SnmpCommunity,
    StpGlobal,
    StpPort,
    StpSnapshot,
    SwitchCounters,
    SwitchInfo,
    SyslogEntry,
    TimeInfo,
    UserAccount,
    Vlan,
    VlanMember,
)

# --------------------------------------------------------------------------
# shared helpers
# --------------------------------------------------------------------------

_LANG_RE = re.compile(
    r"^lang\('(?P<ns>[^']*)','(?P<key>[^']*)'(?:,\[(?P<args>[^\]]*)\])?\)$"
)

_MAC_STATUS_LABELS = {
    "lblCpuPort": "cpu",
    "lblMacTypeDynamic": "dynamic",
    "lblMacTypeStatic": "static",
    "lblMacTypeManage": "management",
    "lblMacTypeIPHostLearned": "ip-host",
}

_SERVICE_LABELS = {
    "lblTelnet": "telnet",
    "lblSsh": "ssh",
    "lblHttp": "http",
    "lblHttps": "https",
    "lblSnmp": "snmp",
}

_VLAN_MODE_MAP = {0: "access", 1: "trunk", 2: "hybrid"}


def _unwrap_lang(value: Any) -> Tuple[Optional[str], List[str]]:
    """Split a ``lang(...)`` template into (i18n key, numeric args).

    Non-template values pass through as (value, []).
    """
    if not isinstance(value, str):
        return None, []
    m = _LANG_RE.match(value.strip())
    if not m:
        return value, []
    args = [a.strip() for a in (m.group("args") or "").split(",") if a.strip()]
    return m.group("key"), args


def _payload(raw: Dict[str, Any]) -> Any:
    """Most endpoints wrap content in {'data': ...}; some don't."""
    if isinstance(raw, dict) and "data" in raw and len(raw) <= 2:
        return raw["data"]
    return raw


def _to_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _parse_membership(membership: str) -> List[Tuple[int, str]]:
    """'1UP, 5T, 120F' -> [(1,'UP'), (5,'T'), (120,'F')]; drops 4095P placeholder."""
    out: List[Tuple[int, str]] = []
    for token in (membership or "").split(","):
        token = token.strip()
        if not token or token == "4095P":
            continue
        digits = token[: len(token) - len(token.lstrip("0123456789"))]
        kind = token[len(digits):]
        if digits and kind in ("T", "UP", "F"):
            out.append((int(digits), kind))
    return out


def _mac_valid(mac: Any) -> bool:
    return bool(mac) and bool(re.match(r"^[0-9A-Fa-f:.-]{11,17}$", str(mac)))


_LABEL_OVERRIDES = {
    "lblNS": "not_supported",
    "lblNA": "n_a",
    "txtNA": "n_a",
    "lblInsert": "inserted",
    "lblNormal": "normal",
    "lblReadOnly": "read_only",
    "lblReadonly": "read_only",
    "lblReadWrite": "read_write",
    "lblBasic": "basic",
}

_ROUTE_TYPE_NAMES = {0: "default", 1: "dhcp", 2: "directly_connected", 3: "static"}
# mapping verified against the device's own UI (ipconf_ipv4_route.html routeType[])


def _label(value: Any) -> Optional[str]:
    """Normalize a value that may be a lang() template into a snake_case token.

    ``lang('stp','txtForwarding')`` -> 'forwarding'; plain strings pass
    through; firmware placeholders ('---', '') become None.
    """
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or set(value) == {"-"}:
        return None
    if not value.startswith("lang("):
        return value  # plain firmware string, not an i18n template
    key, _ = _unwrap_lang(value)
    if key is None:
        return value
    if key in _LABEL_OVERRIDES:
        return _LABEL_OVERRIDES[key]
    token = re.sub(r"^(txt|lbl)", "", key)
    token = re.sub(r"(?<!^)(?=[A-Z])", "_", token).lower()
    return token or None


def _port_names_or_indexes(sections: Dict[str, Any], count: int) -> List[Optional[str]]:
    """Display names from port_bandwidth ticks where available (index < 8),
    None beyond the panel."""
    names = _vimin_port_names(sections)
    return [names[i] if i < len(names) else None for i in range(count)]


def _opt_float(value: Any) -> Optional[float]:
    if not isinstance(value, str):
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", value)
    return float(m.group()) if m else None


_DDM_PWR_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*\(\s*(-?\d+(?:\.\d+)?)\s*dBm\s*\)")


def _opt_power(value: Any) -> Tuple[Optional[float], Optional[float]]:
    """' 0.66(-1.83 dBm)' -> (mw, dbm)."""
    if not isinstance(value, str):
        return None, None
    m = _DDM_PWR_RE.search(value)
    return (float(m.group(1)), float(m.group(2))) if m else (None, None)


# --------------------------------------------------------------------------
# VM-S100-0800MS (VIMIN) — validated against live fw 3.5.0.10
# --------------------------------------------------------------------------

def vimin_info(sections: Dict[str, Any]) -> SwitchInfo:
    sysd = _payload(sections.get("system_info", {})) or {}
    cpud = _payload(sections.get("cpu_memory", {})) or {}

    uptime: Optional[int] = None
    key, args = _unwrap_lang(sysd.get("sysUpTime"))
    if key == "txtSysUptimeArg" and len(args) == 4:
        nums = [_to_int(a) for a in args]
        if len(nums) == 4 and all(isinstance(n, int) for n in nums):
            d, h, m, s = nums
            uptime = d * 86400 + h * 3600 + m * 60 + s

    services: Optional[Services] = None
    methods = sysd.get("methods")
    if isinstance(methods, list):
        fields: Dict[str, bool] = {}
        for item in methods:
            if not isinstance(item, dict):
                continue
            label, _ = _unwrap_lang(item.get("txt"))
            field = _SERVICE_LABELS.get(label or "")
            if field:
                fields[field] = bool(item.get("state"))
        if fields:
            services = Services(**fields)

    ipv6 = sysd.get("currIpv6")
    if isinstance(ipv6, str):
        ipv6 = [ipv6]

    return SwitchInfo(
        hostname=sysd.get("hostname") or None,
        sys_object_id=sysd.get("sysObjID") or None,
        firmware_version=sysd.get("fwVer") or None,
        firmware_date=sysd.get("fwDate") or None,
        loader_version=sysd.get("loaderVer") or None,
        base_mac=sysd.get("sysMac") or None,
        ipv4=sysd.get("currIpv4") or None,
        ipv6=[str(x) for x in (ipv6 or [])],
        location=sysd.get("location") or None,
        contact=sysd.get("contact") or None,
        system_time=(sysd.get("sysCurrTime") or "").strip() or None,
        uptime_seconds=uptime,
        cpu_pct=_to_int(cpud.get("cpu")),
        mem_pct=_to_int(cpud.get("mem")),
        services=services,
    )


def _vimin_port_names(sections: Dict[str, Any]) -> List[str]:
    """Canonical port names from port_bandwidth ticks ([[0,'TE1'],...])."""
    bw = _payload(sections.get("port_bandwidth", {})) or {}
    names: List[str] = []
    for tick in bw.get("ticks", []):
        if isinstance(tick, list) and len(tick) == 2 and str(tick[1]).strip():
            names.append(str(tick[1]).strip())
    return names


def vimin_ports(sections: Dict[str, Any]) -> List[Port]:
    panel = (_payload(sections.get("panel_info", {})) or {}).get("ports", [])
    vlan_port = (_payload(sections.get("vlan_port", {})) or {}).get("ports", [])
    membership = (_payload(sections.get("vlan_membership", {})) or {}).get("ports", [])
    names = _vimin_port_names(sections)

    count = max(len(panel), len(vlan_port), len(membership))
    ports: List[Port] = []
    for i in range(count):
        p = panel[i] if i < len(panel) else {}
        vp = vlan_port[i] if i < len(vlan_port) else {}
        mem = membership[i] if i < len(membership) else {}

        tagged: List[int] = []
        untagged: List[int] = []
        forbidden: List[int] = []
        for vlan_id, kind in _parse_membership(mem.get("adminVlans", "")):
            {"T": tagged, "UP": untagged, "F": forbidden}[kind].append(vlan_id)

        speed = _to_int(p.get("speed")) if p else None
        dup = p.get("dupFull") if p else None
        ports.append(
            Port(
                index=i,
                name=names[i] if i < len(names) else (f"port{i + 1}" if p else None),
                present=bool(p),
                link_up=p.get("linkup") if p else None,
                autonegotiate=p.get("autoNego") if p else None,
                speed_mbps=speed,
                duplex=("full" if dup else "half") if isinstance(dup, bool) else None,
                media=p.get("media") if p else None,
                vlan_mode=(_VLAN_MODE_MAP.get(vp["mode"]) if isinstance(vp.get("mode"), int) else None),
                pvid=_to_int(vp.get("pvid")) if vp else None,
                uplink=vp.get("uplink") if vp else None,
                tagged=tagged,
                untagged=untagged,
                forbidden=forbidden,
            )
        )
    return ports


def vimin_vlans(sections: Dict[str, Any]) -> List[Vlan]:
    cfg = _payload(sections.get("vlan_config", {})) or {}
    membership = (_payload(sections.get("vlan_membership", {})) or {}).get("ports", [])
    names = _vimin_port_names(sections)

    by_id: Dict[int, Vlan] = {}
    for entry in cfg.get("vlans", []):
        vlan_id = _to_int(entry.get("val"))
        if vlan_id is None:
            continue
        by_id[vlan_id] = Vlan(vlan_id=vlan_id, name=entry.get("name") or None)

    for i, mem in enumerate(membership):
        port_name = names[i] if i < len(names) else None
        for vlan_id, kind in _parse_membership(mem.get("adminVlans", "")):
            vlan = by_id.get(vlan_id)
            if vlan is None:  # membership references an unknown VLAN — keep it visible
                vlan = Vlan(vlan_id=vlan_id)
                by_id[vlan_id] = vlan
            if kind != "F":
                vlan.members.append(
                    VlanMember(port_index=i, port_name=port_name, tagged=(kind == "T"))
                )
    return sorted(by_id.values(), key=lambda v: v.vlan_id)


def vimin_mac_table(sections: Dict[str, Any]) -> List[MacEntry]:
    merged: Dict[Tuple[str, Optional[int]], MacEntry] = {}

    def source(key: str) -> List[Dict[str, Any]]:
        d = _payload(sections.get(key, {})) or {}
        entries = d.get("entries", []) if isinstance(d, dict) else []
        return [e for e in entries if isinstance(e, dict)]

    def merge(entry: Dict[str, Any], default_type: Optional[str]) -> None:
        if not _mac_valid(entry.get("macAddr")):
            return  # firmware pads tables with empty placeholder rows
        mac = str(entry["macAddr"]).upper()
        vlan_id = _to_int(entry.get("vlan"))
        vlan_id = vlan_id if vlan_id else None
        key = (mac, vlan_id)

        port = entry.get("port") or None
        if port:
            label, _ = _unwrap_lang(port)
            port = _MAC_STATUS_LABELS.get(label or "", port)

        etype = entry.get("type") or None
        if etype:
            label, _ = _unwrap_lang(etype)
            etype = _MAC_STATUS_LABELS.get(label or "", str(etype))
        else:
            etype = default_type

        existing = merged.get(key)
        if existing is None:
            merged[key] = MacEntry(mac=mac, vlan_id=vlan_id, port=port, entry_type=etype)
        else:
            if existing.port is None and port:
                existing.port = port
            if existing.entry_type in (None, "dynamic") and etype not in (None, "dynamic"):
                existing.entry_type = etype

    for e in source("mac_static"):
        merge(e, "static")
    for e in source("mac_dynamic"):
        merge(e, "dynamic")
    for e in source("mac_status"):
        merge(e, None)

    return sorted(merged.values(), key=lambda m: (m.vlan_id or 0, m.mac))


def vimin_lldp(sections: Dict[str, Any]) -> List[LldpNeighbor]:
    raw = sections.get("lldp_neighbors")
    neighbors = []
    if isinstance(raw, dict):
        neighbors = raw.get("neighbors", [])
    out: List[LldpNeighbor] = []
    for n in neighbors:
        if not isinstance(n, dict):
            continue
        out.append(
            LldpNeighbor(
                local_port=n.get("localPort") or n.get("local_port"),
                chassis_id=n.get("chassisId") or n.get("chassis_id"),
                system_name=n.get("systemName") or n.get("system_name"),
                port_id=n.get("portId") or n.get("port_id"),
                **{k: v for k, v in n.items()
                   if k not in ("localPort", "local_port", "chassisId",
                                "chassis_id", "systemName", "system_name",
                                "portId", "port_id")},
            )
        )
    return out


def vimin_syslog(sections: Dict[str, Any]) -> List[SyslogEntry]:
    data = _payload(sections.get("syslog", {})) or {}
    out: List[SyslogEntry] = []
    for log in data.get("logs", []):
        if isinstance(log, dict):
            out.append(
                SyslogEntry(
                    time=log.get("time"),
                    severity=log.get("sev"),
                    description=log.get("desc"),
                )
            )
    return out


# ---- extended resources (2026-11 discovery, live-validated fw 3.5.0.10) ----

def vimin_l3(sections: Dict[str, Any]) -> L3Snapshot:
    ipd = _payload(sections.get("mgmt_ip", {})) or {}
    dnsd = _payload(sections.get("dns", {})) or {}
    timed = _payload(sections.get("time", {})) or {}
    routes_raw = _payload(sections.get("l3_routes", {})) or {}
    arp_raw = _payload(sections.get("l3_arp", {})) or {}
    ifd = _payload(sections.get("l3_interfaces", {})) or {}

    routes = []
    for r in routes_raw.get("route", []):
        rtype = _to_int(r.get("type"))
        routes.append(
            Route(
                dest=r.get("dip") or None,
                prefix_len=_to_int(r.get("plen")),
                type=rtype,
                type_name=_ROUTE_TYPE_NAMES.get(rtype),
                next_hop=r.get("nextHop") or None,
                metric=_to_int(r.get("metric")),
                admin_distance=_to_int(r.get("adminDistance")),
                interface=r.get("intf") or None,
            )
        )

    arp = [
        ArpEntry(
            ip=e.get("ip") or None,
            mac=(str(e["mac"]).upper() if e.get("mac") else None),
            vlan_id=_to_int(e.get("vlan")),
            interface=e.get("intf") or None,
            static=e.get("static"),
        )
        for e in arp_raw.get("entries", [])
        if _mac_valid(e.get("mac")) or e.get("ip")
    ]

    interfaces = []
    if isinstance(ifd, dict):
        for i in ifd.get("intf", ifd.get("entries", [])):
            if isinstance(i, dict):
                ip = i.get("ip") or i.get("addr")
                if ip:
                    interfaces.append(str(ip))

    servers = [
        str(d["ip"])
        for d in sorted(dnsd.get("dnss", []), key=lambda d: d.get("pref", 0))
        if isinstance(d, dict) and d.get("ip")
    ]

    return L3Snapshot(
        mgmt=MgmtIp(
            mode=ipd.get("type") or None,
            ip=ipd.get("staticIp") or ipd.get("ip") or None,
            netmask=ipd.get("staticMask") or None,
            gateway=ipd.get("adminGw") or None,
            operating_gateway=ipd.get("operGw") or None,
            ipv6=ipd.get("staticIpv6") if ipd.get("staticIpv6") not in ("::", "") else None,
            link_local=ipd.get("linkLocalAddr") or None,
        ),
        dns=DnsInfo(enabled=bool(dnsd.get("state")), servers=[str(s) for s in servers if s]),
        time=TimeInfo(
            sntp_enabled=timed.get("sntp"),
            sntp_server=timed.get("srvHost") or None,
            epoch=_to_int(timed.get("time")),
            system_time=(timed.get("timeStr") or "").strip() or None,
            timezone_minutes=_to_int(timed.get("timezone")),
        ),
        interfaces=interfaces,
        routes=routes,
        arp=arp,
        arp_aging_seconds=_to_int(arp_raw.get("aging")),
    )


def vimin_stp(sections: Dict[str, Any]) -> StpSnapshot:
    g = _payload(sections.get("stp_global", {})) or {}
    ports_raw = (_payload(sections.get("stp_ports", {})) or {}).get("ports", [])
    names = _port_names_or_indexes(sections, len(ports_raw))

    glob = StpGlobal(
        enabled=g.get("enable"),
        mode=g.get("mode") or None,
        priority=_to_int(g.get("pri")),
        hello_seconds=_to_int(g.get("helloTime")),
        max_age_seconds=_to_int(g.get("age")),
        fwd_delay_seconds=_to_int(g.get("fwdDelay")),
        tx_hold_count=_to_int(g.get("txCnt")),
        region_name=g.get("regionName") or None,
        revision=_to_int(g.get("revision")),
        max_hop=_to_int(g.get("maxhop")),
        bridge_id=(g.get("bridgeId") or "").strip() or None,
        root_bridge_id=(g.get("rootBridgeId") or "").strip() or None,
        root_cost=_to_int(g.get("rootCost")),
        topology_change_count=_to_int(g.get("tcCnt")),
    )

    ports = [
        StpPort(
            index=i,
            name=names[i],
            enabled=p.get("enable"),
            priority=_to_int(p.get("pri")),
            path_cost=_to_int(p.get("pathcost")),
            bpdu_guard=p.get("bpduGuard"),
            bpdu_filter=p.get("bpduFilter"),
            edge=p.get("edge_oper"),
            point_to_point=p.get("p2p_oper"),
            role=_label(p.get("role")),
            state=_label(p.get("state")),
            designated_bridge=(p.get("desgBridge") or "").strip() or None,
            designated_port=(p.get("desgPortId") or "").strip() or None,
            designated_cost=_to_int(p.get("desgCost")),
        )
        for i, p in enumerate(ports_raw)
    ]
    return StpSnapshot(global_config=glob, ports=ports)


def vimin_optics(sections: Dict[str, Any]) -> List[OpticsPort]:
    ports_raw = (_payload(sections.get("optical_ddm", {})) or {}).get("ports", [])
    names = _port_names_or_indexes(sections, len(ports_raw))
    out: List[OpticsPort] = []
    for i, p in enumerate(ports_raw):
        tx_mw, tx_dbm = _opt_power(p.get("txPwr"))
        rx_mw, rx_dbm = _opt_power(p.get("rxPwr"))
        temp = _opt_float(p.get("temp"))
        ddm = temp is not None or tx_dbm is not None or rx_dbm is not None
        out.append(
            OpticsPort(
                index=_to_int(p.get("port")) or i,
                name=names[i],
                present=_label(p.get("oe")) == "inserted",
                loss_of_signal=_label(p.get("los")),
                temperature_c=temp,
                voltage_v=_opt_float(p.get("volt")),
                bias_ma=_opt_float(p.get("bias")),
                tx_power_mw=tx_mw,
                tx_power_dbm=tx_dbm,
                rx_power_mw=rx_mw,
                rx_power_dbm=rx_dbm,
                ddm_supported=ddm,
            )
        )
    return out


def _mirror_port_list(value: Any) -> List[str]:
    if not isinstance(value, str):
        return []
    parts = [p.strip() for p in re.split(r"[,+]", value)]
    return [p for p in parts if p and set(p) != {"-"}]


def vimin_mirror(sections: Dict[str, Any]) -> List[MirrorSession]:
    sessions = (_payload(sections.get("mirror_sessions", {})) or {}).get("sessions", [])
    out: List[MirrorSession] = []
    for i, s in enumerate(sessions):
        state = _label(s.get("state"))
        out.append(
            MirrorSession(
                index=i,
                enabled=(state == "enabled") if state else None,
                ingress_mirror=bool(s.get("ingressState")) if "ingressState" in s else None,
                source_rx=_mirror_port_list(s.get("sourceRxPort")),
                source_tx=_mirror_port_list(s.get("sourceTxPort")),
                destination=_label(s.get("dstPort")),
            )
        )
    return out


def vimin_firmware(sections: Dict[str, Any]) -> FirmwareStatus:
    d = _payload(sections.get("firmware_images", {})) or {}
    names = (_payload(sections.get("firmware_img", {})) or {}).get("imgName", [])
    return FirmwareStatus(
        dual_image_enabled=bool(d.get("dual_enable")),
        active_index=_to_int(d.get("actIdx")),
        selected_index=_to_int(d.get("selIdx")),
        active_version=(d.get("actVer") or "").strip() or None,
        active_image=(d.get("actName") or "").strip() or None,
        active_size_bytes=_to_int(d.get("actSize")),
        active_time=(d.get("actTime") or "").strip() or None,
        image_names=[str(n).strip() for n in names if str(n).strip()],
    )


def vimin_users(sections: Dict[str, Any]) -> List[UserAccount]:
    users = (_payload(sections.get("local_users", {})) or {}).get("users", [])
    return [
        UserAccount(username=str(u["user"]), privilege=_to_int(u.get("priv")))
        for u in users
        if isinstance(u, dict) and u.get("user")
    ]


def vimin_snmp(sections: Dict[str, Any]) -> List[SnmpCommunity]:
    comms = (_payload(sections.get("snmp_communities", {})) or {}).get("communities", [])
    return [
        SnmpCommunity(
            index=_to_int(c.get("idx")),
            community=c.get("commStr") or None,
            version_type=_label(c.get("commType")),
            access=_label(c.get("accessMode")),
            view=c.get("viewName") or None,
        )
        for c in comms
        if isinstance(c, dict) and c.get("commStr")
    ]


VIMIN_NORMALIZERS: Dict[str, Callable[[Dict[str, Any]], Any]] = {
    "info": vimin_info,
    "ports": vimin_ports,
    "vlans": vimin_vlans,
    "mac_table": vimin_mac_table,
    "lldp": vimin_lldp,
    "syslog": vimin_syslog,
    "l3": vimin_l3,
    "stp": vimin_stp,
    "optics": vimin_optics,
    "mirror": vimin_mirror,
    "firmware": vimin_firmware,
    "users": vimin_users,
    "snmp": vimin_snmp,
}

# canonical model key -> resource -> normalizer
NORMALIZERS: Dict[str, Dict[str, Callable]] = {
    "vm-s100-0800ms": VIMIN_NORMALIZERS,
}


def get_normalizer(model_key: str, resource: str) -> Callable[[Dict[str, Any]], Any]:
    from .pool import UnsupportedModel

    model_map = NORMALIZERS.get(model_key)
    if not model_map or resource not in model_map:
        raise UnsupportedModel(model_key, sorted(NORMALIZERS))
    return model_map[resource]
