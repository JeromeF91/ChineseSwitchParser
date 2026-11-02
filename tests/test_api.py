"""API tests with a stubbed pool — no network, no switches."""

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from csp_api.app import create_app
from csp_api.pool import SwitchUnavailable
from csp_api.registry import HostConfig

FIXTURE = Path(__file__).parent / "fixtures" / "vimin33_raw.json"

HOST = HostConfig(
    name="vimin-test",
    url="http://10.41.8.33",
    username="admin",
    password="admin",
    model="vm-s100-0800ms",
)


class StubPool:
    def __init__(self, raw, fail=False):
        self.raw = raw
        self.fail = fail

    def model_key(self, cfg):
        return cfg.model or "vm-s100-0800ms"

    def get_client(self, cfg):
        raw_keys = list(self.raw)

        class C:
            api_endpoints = {k: f"cgi/get.cgi?cmd={k}" for k in raw_keys}

        return C()

    def fetch_raw(self, cfg, section_keys):
        if self.fail:
            raise SwitchUnavailable("stub: switch down")
        return {k: self.raw[k] for k in section_keys if k in self.raw}, []


@pytest.fixture()
def raw():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture()
def client(raw, monkeypatch):
    monkeypatch.setenv("CSP_API_TOKEN", "test-token")
    app = create_app(pool=StubPool(raw), registry={HOST.name: HOST})
    return TestClient(app)


AUTH = {"Authorization": "Bearer test-token"}


def test_healthz_no_auth_required(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["auth_enabled"] is True
    assert body["hosts"] == 1


def test_missing_token_rejected(client):
    assert client.get("/switches").status_code == 401
    assert client.get("/switches", headers=AUTH).status_code == 200


def test_unknown_host_404(client):
    r = client.get("/switches/nosuch/info", headers=AUTH)
    assert r.status_code == 404
    assert "vimin-test" in r.json()["detail"]


def test_info_endpoint(client):
    r = client.get("/switches/vimin-test/info", headers=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert body["host"] == "vimin-test"
    assert body["model"] == "vm-s100-0800ms"
    assert body["data"]["hostname"] == "SW-TOR01-VIM10g"
    assert body["data"]["services"]["ssh"] is True
    assert body["fetched_at"]


def test_ports_and_vlans_endpoints(client):
    r = client.get("/switches/vimin-test/ports", headers=AUTH)
    assert r.status_code == 200
    ports = r.json()["data"]
    assert ports[0]["name"] == "TE1"
    assert ports[0]["speed_mbps"] == 10000

    r = client.get("/switches/vimin-test/vlans", headers=AUTH)
    assert r.status_code == 200
    vlans = r.json()["data"]
    assert any(v["vlan_id"] == 5 and v["name"] == "TOR02-IOT" for v in vlans)


def test_mac_table_hyphenated_route(client):
    r = client.get("/switches/vimin-test/mac-table", headers=AUTH)
    assert r.status_code == 200
    assert all("mac" in e for e in r.json()["data"])


def test_switch_unavailable_502(raw, monkeypatch):
    monkeypatch.setenv("CSP_API_TOKEN", "test-token")
    app = create_app(pool=StubPool(raw, fail=True), registry={HOST.name: HOST})
    c = TestClient(app)
    r = c.get("/switches/vimin-test/info", headers=AUTH)
    assert r.status_code == 502


def test_unsupported_model_501(raw, monkeypatch):
    monkeypatch.setenv("CSP_API_TOKEN", "test-token")
    sodola = HostConfig(
        name="sodola-34", url="http://10.41.8.34",
        username="admin", password="admin", model="sl-swtg124as",
    )

    class SODPool(StubPool):
        def model_key(self, cfg):
            return cfg.model

    app = create_app(pool=SODPool(raw), registry={sodola.name: sodola})
    c = TestClient(app)
    r = c.get("/switches/sodola-34/info", headers=AUTH)
    assert r.status_code == 501
    assert "vm-s100-0800ms" in r.json()["detail"]  # tells caller what IS supported


def test_raw_endpoint_sections(client):
    r = client.get("/switches/vimin-test/raw?sections=system_info,cpu_memory", headers=AUTH)
    assert r.status_code == 200
    assert set(r.json()["data"]) == {"system_info", "cpu_memory"}


def test_registry_rejects_bad_names(tmp_path):
    from csp_api.registry import RegistryError, load_registry

    bad = tmp_path / "hosts.yaml"
    bad.write_text("switches:\n  - name: Bad_Name\n    url: http://x\n    username: u\n    password: p\n")
    with pytest.raises(RegistryError):
        load_registry(bad)


def test_registry_env_password(tmp_path, monkeypatch):
    from csp_api.registry import load_registry

    monkeypatch.setenv("TEST_CSP_PW", "s3cret")
    f = tmp_path / "hosts.yaml"
    f.write_text(
        "switches:\n  - name: h1\n    url: 10.0.0.1\n    username: admin\n    password: env:TEST_CSP_PW\n"
    )
    hosts = load_registry(f)
    assert hosts["h1"].password == "s3cret"
    assert hosts["h1"].url == "http://10.0.0.1"
