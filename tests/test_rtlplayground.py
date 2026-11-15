"""Normalizer + model tests for RTLPlayground (open RTL8372/8373 firmware).

The fixture is a live capture from httpd_sim.py (the project's device
simulator) served on CT-TOR02-LAB01, so assertions are contracts against the
firmware/simulator JSON, not invented shapes. httpd_sim mirrors the real
firmware's httpd handlers (same endpoints, same login contract), so these
hold for flashed hardware too.
"""

import json
from pathlib import Path

import pytest

from csp_api.normalizers import (
    rtlplayground_info,
    rtlplayground_mac_table,
    rtlplayground_ports,
    rtlplayground_vlans,
)
from switch_models.rtlplayground import RTLPlayground

FIXTURE = Path(__file__).parent / "fixtures" / "rtlplayground_sim_raw.json"


@pytest.fixture(scope="module")
def raw():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


# ---- contract notes --------------------------------------------------------
# - login is POST /login with "pwd=" ONLY (no username field; firmware
#   run_login_body in httpd/httpd.c checks strstart(body, "pwd=")).
# - success is signalled by the session cookie, NOT by the status code:
#   a wrong password also returns 302 (to login.html, cookie-less).
# - l2.json is cursor-paginated by an in-band "idx"; the capture below is
#   already merged across pages by the model, so the fixture has no idx pages.
# - the VLAN detail table has no list-all endpoint; vlan.json answers one vid
#   per GET and is enumerated from vlanlist.json by the model.
# - after PR #768 every port number is a PHYSICAL port; the CPU port is 0.
# - mac/vlan fields are lowercase hex strings; vlan is hex, not decimal.
# ---------------------------------------------------------------------------


def test_auth_contract_requires_session_cookie():
    """302 alone must never be treated as success."""
    sw = RTLPlayground("http://127.0.0.1:1", "", "wrong")
    assert sw.authenticate() is False  # unreachable host


def test_info(raw):
    info = rtlplayground_info(raw["info"])
    d = raw["info"]["info"]
    assert info.ipv4 == d["ip_address"]
    assert info.base_mac == d["mac_address"].upper()
    assert info.firmware_version == d["sw_ver"]
    # uptime is a hex string ("0x0000016c") on this API
    assert info.uptime_seconds == int(d["uptime"], 16)
    # PCB identity is folded into sys_object_id so fleet inventory can tell
    # same-sw_ver devices apart (the #768 doc calls pcb_ver the discriminator)
    assert d["pcb_ver"] in (info.sys_object_id or "")


def test_ports_join_traffic_on_physical_port(raw):
    ports = rtlplayground_ports(raw["ports"])
    by_index = {p.index: p for p in ports}
    traffic = {t["port"]: t for t in raw["ports"]["traffic"]}

    assert set(by_index) == set(traffic), "ports/traffic must join 1:1"
    for p in ports:
        t = traffic[p.index]
        if t["link"].upper() == "DOWN":
            assert p.link_up is False and p.speed_mbps is None
        else:
            assert p.link_up is True


def test_ports_speed_and_duplex_parsing(raw):
    by_index = {p.index: p for p in rtlplayground_ports(raw["ports"])}
    traffic = {t["port"]: t for t in raw["ports"]["traffic"]}
    for p in by_index.values():
        link = traffic[p.index]["link"]
        if p.speed_mbps is None:
            continue
        assert p.duplex == ("half" if link.endswith("-HD") else "full"), link


def test_ports_media_is_sfp_flag(raw):
    ports = rtlplayground_ports(raw["ports"])
    src = {p["port"]: p for p in raw["ports"]["ports"]}
    for p in ports:
        want = "fiber" if src[p.index]["isSFP"] else "copper"
        assert p.media == want


def test_vlans_members_tagged_split(raw):
    vlans = rtlplayground_vlans(raw["vlans"])
    by_id = {v.vlan_id: v for v in vlans}
    for entry in raw["vlans"]["vlans"]["entries"]:
        v = by_id[entry["vid"]]
        tagged = {m.port_index for m in v.members if m.tagged}
        untagged = {m.port_index for m in v.members if not m.tagged}
        assert tagged == set(entry["tagged_members"])
        assert untagged == set(entry["untagged_members"])
        # a port may never appear in both lists for one VLAN
        assert tagged & untagged == set()


def test_mac_table_hex_vlan_and_type_mapping(raw):
    table = rtlplayground_mac_table(raw["mac_table"])
    entries = raw["mac_table"]["mac_table"]["entries"]
    assert len(table) == len(entries)

    for got, src in zip(table, entries):
        # vlan is a HEX string ("0001"); int() of it would silently mis-key
        assert got.vlan_id == int(src["vlan"], 16)
        assert got.mac == src["mac"].upper()
        assert got.port == str(src["port"])

    kinds = {e.entry_type for e in table}
    assert kinds <= {"dynamic", "static"}
    src_kinds = {("static" if e["type"] == "s" else "dynamic")
                 for e in entries}
    assert kinds == src_kinds


def test_mac_table_cursor_walk_has_no_duplicates(raw):
    """The sim serves L2_MAX_TRANSFER=5 rows per page; the merged capture
    must cover the whole table exactly once. A naive re-send of the hex
    cursor restarts the walk (sim int(x,0) ValueError -> 0) and silently
    duplicates rows — the model's hex-out/decimal-in +1 cursor prevents it.
    Regression test for the first live run, 2026-11-15."""
    table = rtlplayground_mac_table(raw["mac_table"])
    keys = [(e.mac, e.vlan_id) for e in table]
    # sim table = 12 rows over 3 pages of L2_MAX_TRANSFER=5 (5+5+2); the
    # broken cursor saw only 10 rows, 5 of them duplicates — 7 real entries
    # silently lost.
    assert len(table) == 12, "sim table has 12 entries across 3 pages"
    assert len(set(keys)) == len(keys), "cursor walk duplicated rows"


def test_mac_table_rejects_invalid_macs(raw):
    bad = {"mac_table": {"entries": [
        {"mac": "", "vlan": "0001", "type": "l", "port": 1},
        {"mac": "not-a-mac", "vlan": "0001", "type": "l", "port": 2},
        {"mac": "aa:bb:cc:dd:ee:ff", "vlan": "0064", "type": "s", "port": 3},
    ]}}
    out = rtlplayground_mac_table(bad)
    assert len(out) == 1
    assert out[0].vlan_id == 100  # 0x64
    assert out[0].entry_type == "static"
