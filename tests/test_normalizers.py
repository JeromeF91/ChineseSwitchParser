"""Normalizer tests driven by a real capture from SW-TOR01-VIM10g (fw 3.5.0.10).

The fixture is live production data, so these assertions are contracts
against firmware quirks, not invented shapes.
"""

import json
from pathlib import Path

import pytest

from csp_api.normalizers import (
    _parse_membership,
    _unwrap_lang,
    vimin_info,
    vimin_lldp,
    vimin_mac_table,
    vimin_ports,
    vimin_vlans,
)

FIXTURE = Path(__file__).parent / "fixtures" / "vimin33_raw.json"


@pytest.fixture(scope="module")
def raw():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


# ---- helpers ---------------------------------------------------------------

def test_unwrap_lang_template():
    key, args = _unwrap_lang("lang('sys','txtSysUptimeArg',[0,13,27,55])")
    assert key == "txtSysUptimeArg"
    assert args == ["0", "13", "27", "55"]


def test_unwrap_lang_passthrough():
    assert _unwrap_lang("SW-TOR01-VIM10g") == ("SW-TOR01-VIM10g", [])
    assert _unwrap_lang(None) == (None, [])


def test_membership_parser():
    assert _parse_membership("1UP, 5T, 120F, 4095P") == [(1, "UP"), (5, "T"), (120, "F")]
    assert _parse_membership("") == []


# ---- info -------------------------------------------------------------------

def test_info(raw):
    info = vimin_info({"system_info": raw["system_info"], "cpu_memory": raw["cpu_memory"]})
    assert info.hostname == "SW-TOR01-VIM10g"
    assert info.firmware_version == "3.5.0.10"
    assert info.ipv4 == "10.41.8.33"
    assert info.base_mac == "1A:4B:24:A3:BE:DF"
    assert info.ipv6 and info.ipv6[0].startswith("fe80::")
    # sysUpTime arrives as a lang() template: [d, h, m, s]
    assert info.uptime_seconds == 13 * 3600 + 27 * 60 + 55
    assert info.cpu_pct == 0
    assert info.mem_pct == 13
    assert info.services is not None
    assert info.services.ssh is True
    assert info.services.telnet is False
    assert info.services.snmp is True


# ---- ports --------------------------------------------------------------------

def test_ports(raw):
    ports = vimin_ports(
        {
            "panel_info": raw["panel_info"],
            "vlan_port": raw["vlan_port"],
            "vlan_membership": raw["vlan_membership"],
            "port_bandwidth": raw["port_bandwidth"],
        }
    )
    # panel exposes 8 physical ports; vlan sections have 16 rows
    assert len(ports) == 16
    assert sum(1 for p in ports if p.present) == 8

    te1 = ports[0]
    assert te1.name == "TE1"
    assert te1.link_up is True
    assert te1.speed_mbps == 10000
    assert te1.duplex == "full"
    assert te1.media == "fiber"
    assert te1.vlan_mode == "hybrid"
    assert te1.pvid == 1
    assert 5 in te1.tagged and 120 in te1.tagged
    assert 1 in te1.untagged  # 1UP
    assert 1 not in te1.forbidden

    te3 = ports[2]
    assert te3.link_up is False
    assert te3.speed_mbps is None  # down port reports no speed

    # logical rows beyond the panel get no display name
    assert ports[10].name is None
    assert ports[10].present is False


def test_ports_forbidden_membership(raw):
    ports = vimin_ports(
        {
            "panel_info": raw["panel_info"],
            "vlan_port": raw["vlan_port"],
            "vlan_membership": raw["vlan_membership"],
            "port_bandwidth": raw["port_bandwidth"],
        }
    )
    # port2 adminVlans contains '1F' -> forbidden, and '120UP' -> untagged
    assert 1 in ports[2].forbidden
    assert 120 in ports[2].untagged


# ---- vlans --------------------------------------------------------------------

def test_vlans(raw):
    vlans = vimin_vlans({"vlan_config": raw["vlan_config"], "vlan_membership": raw["vlan_membership"]})
    assert len(vlans) >= 22
    by_id = {v.vlan_id: v for v in vlans}
    assert by_id[5].name == "TOR02-IOT"
    assert by_id[190].name == "TOR01-GuestWifi"
    # vlan 1 default is untagged member of TE1
    v1_ports = {(m.port_index, m.tagged) for m in by_id[1].members}
    assert (0, False) in v1_ports
    # vlan 5 tagged on TE1
    assert any(m.port_index == 0 and m.tagged for m in by_id[5].members)
    # '1F' on port2 is forbidden, so port2 must not be a member of vlan 1 at all
    assert 2 not in [m.port_index for m in by_id[1].members]


# ---- mac table ------------------------------------------------------------------

def test_mac_table(raw):
    entries = vimin_mac_table(
        {
            "mac_dynamic": raw["mac_dynamic"],
            "mac_static": raw["mac_static"],
            "mac_status": raw["mac_status"],
        }
    )
    # empty placeholder row in mac_static is dropped
    assert all(e.mac for e in entries)
    by_mac = {(e.mac, e.vlan_id): e for e in entries}
    dyn = by_mac[("00:1C:7F:62:62:16", 120)]
    assert dyn.port == "TE1"
    assert dyn.entry_type == "dynamic"
    # lang('mac','lblCpuPort') port label mapped to 'cpu'
    cpu = by_mac[("1A:4B:24:A3:BE:DF", 120)]
    assert cpu.port == "cpu"


# ---- lldp ------------------------------------------------------------------------

def test_lldp_empty(raw):
    assert vimin_lldp({"lldp_neighbors": raw["lldp_neighbors"]}) == []


def test_lldp_with_neighbor():
    out = vimin_lldp(
        {"lldp_neighbors": {"neighbors": [{"localPort": "TE1", "systemName": "FW-TOR01-OPN01"}]}}
    )
    assert out[0].local_port == "TE1"
    assert out[0].system_name == "FW-TOR01-OPN01"


# ---- extended resources: contracts against the 2026-11 live capture ----------

FIXTURE_EXT = Path(__file__).parent / "fixtures" / "vimin33_ext.json"


@pytest.fixture(scope="module")
def ext():
    return json.loads(FIXTURE_EXT.read_text(encoding="utf-8"))


def test_ext_l3(ext):
    from csp_api.normalizers import vimin_l3

    l3 = vimin_l3(ext)
    assert l3.mgmt.mode == "static"
    assert l3.mgmt.ip == "10.41.8.33"
    assert l3.mgmt.gateway == "10.41.8.62"
    assert l3.dns.enabled is True and l3.dns.servers == ["10.41.8.62"]
    assert l3.time.sntp_enabled is True
    assert l3.time.sntp_server == "10.41.8.62"
    assert l3.time.timezone_minutes == -300
    # default route via the lab firewall + connected /27
    by_dest = {r.dest: r for r in l3.routes}
    assert by_dest["0.0.0.0"].next_hop == "10.41.8.62"
    assert by_dest["10.41.8.32"].prefix_len == 27
    assert by_dest["10.41.8.32"].type_name == "directly_connected"
    # arp entry present, mac uppercased
    arp = l3.arp[0]
    assert arp.ip == "10.41.8.62"
    assert arp.mac == "00:1C:7F:62:62:16"
    assert arp.vlan_id == 120
    assert l3.arp_aging_seconds == 1200
    assert l3.interfaces == []  # no routed L3 interfaces on this unit


def test_ext_stp(ext):
    from csp_api.normalizers import vimin_stp

    stp = vimin_stp(ext)
    assert stp.global_config.enabled is False
    assert stp.global_config.mode == "rstp"
    assert stp.global_config.priority == 32768
    assert len(stp.ports) == 16
    p0 = stp.ports[0]
    assert p0.name == "TE1"
    assert p0.enabled is True
    assert p0.priority == 128
    assert p0.path_cost == 2000
    # lang('stp','txtForwarding') -> 'forwarding'
    assert p0.state == "forwarding"
    assert p0.role == "disabled"


def test_ext_optics(ext):
    from csp_api.normalizers import vimin_optics

    ports = vimin_optics(ext)
    assert len(ports) == 8
    te1 = ports[0]
    assert te1.name == "TE1"
    assert te1.present is True
    assert te1.ddm_supported is True
    assert te1.temperature_c == 38.64
    assert te1.tx_power_dbm == -2.19
    assert te1.rx_power_dbm == -1.83
    assert te1.tx_power_mw == 0.60
    # port 1 module inserted but DDM not reported (lblNS)
    p1 = ports[1]
    assert p1.present is True
    assert p1.ddm_supported is False
    assert p1.temperature_c is None


def test_ext_mirror(ext):
    from csp_api.normalizers import vimin_mirror

    sessions = vimin_mirror(ext)
    assert len(sessions) == 4
    assert all(s.enabled is False for s in sessions)
    assert all(s.source_rx == [] and s.destination is None for s in sessions)


def test_ext_firmware(ext):
    from csp_api.normalizers import vimin_firmware

    fw = vimin_firmware(ext)
    assert fw.dual_image_enabled is False
    assert fw.active_size_bytes == 10720270
    assert fw.active_time == "2025-04-22 14:02:50"


def test_ext_users(ext):
    from csp_api.normalizers import vimin_users

    users = vimin_users(ext)
    assert len(users) == 1
    assert users[0].username == "admin"
    assert users[0].privilege == 15


def test_ext_snmp(ext):
    from csp_api.normalizers import vimin_snmp

    comms = vimin_snmp(ext)
    assert len(comms) == 1
    assert comms[0].community == "public"
    assert comms[0].access == "read_only"
    assert comms[0].version_type == "basic"


def test_label_helper():
    from csp_api.normalizers import _label

    assert _label("lang('stp','txtForwarding')") == "forwarding"
    assert _label("lang('diag','lblNS')") == "not_supported"
    assert _label("lang('snmp','lblReadOnly')") == "read_only"
    assert _label("---") is None
    assert _label("") is None
    assert _label("SFP/SFP+") == "SFP/SFP+"
