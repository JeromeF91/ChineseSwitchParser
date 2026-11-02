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
    LldpNeighbor,
    MacEntry,
    Port,
    Services,
    SwitchCounters,
    SwitchInfo,
    SyslogEntry,
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


VIMIN_NORMALIZERS: Dict[str, Callable[[Dict[str, Any]], Any]] = {
    "info": vimin_info,
    "ports": vimin_ports,
    "vlans": vimin_vlans,
    "mac_table": vimin_mac_table,
    "lldp": vimin_lldp,
    "syslog": vimin_syslog,
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
