# ChineseSwitchParser REST API (`csp_api`)

Read-only, normalized HTTP API over the `switch_models` package. One
contract for every supported switch: consumers never see per-vendor
payload dialects.

## Design decisions

- **Named host registry.** Switch credentials live server-side in
  `hosts.yaml` and never travel through the API. Callers reference
  hosts by name: `/switches/vimin-33/vlans`.
- **Normalized schema first.** Each supported model maps its quirks
  (i18n `lang(...)` templates, placeholder rows, `T/UP/F` VLAN
  membership strings, index joins across sections) into the Pydantic
  models in `csp_api/schemas.py`. Fields are `null` when a device
  doesn't report them — never guessed.
- **Session pool.** One client instance per host; re-auth once per
  snapshot with a single retry per failed section.
- **Raw passthrough.** Unsupported models and exotic sections are
  reachable via `/switches/{name}/raw` from day one, so normalizers
  can be added incrementally.
- **LAN-only by design.** These switches hold admin credentials. The
  API must bind loopback/LAN; never expose it through any inbound
  surface.

## Setup

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt -r requirements-api.txt
cp hosts.yaml.example hosts.yaml   # git-ignored; edit hosts
export CSP_API_TOKEN=<generate a long random string>
export CSP_HOSTS_FILE=hosts.yaml
.venv/Scripts/uvicorn csp_api.app:app --host 127.0.0.1 --port 8787
```

Interactive docs: `http://127.0.0.1:8787/docs` (OpenAPI).

## Endpoints (v1, all read-only)

| Endpoint | Notes |
|---|---|
| `GET /healthz` | no auth; reports auth mode + supported models |
| `GET /switches` | registry listing |
| `GET /switches/{name}/detect` | resolved model key |
| `GET /switches/{name}/info` | hostname, firmware, IP, uptime, CPU/RAM, mgmt services |
| `GET /switches/{name}/ports` | link/speed/duplex/media + PVID, mode, tagged/untagged/forbidden VLANs |
| `GET /switches/{name}/vlans` | VLAN id/name + members (tagged flag) |
| `GET /switches/{name}/mac-table` | merged dynamic/static/status, placeholders dropped |
| `GET /switches/{name}/lldp` | neighbors (may be empty depending on firmware) |
| `GET /switches/{name}/syslog` | device log entries |
| `GET /switches/{name}/l3` | mgmt IP/mask/gw, DNS, SNTP/time, routes (typed), ARP |
| `GET /switches/{name}/stp` | STP/RSTP global + per-port role/state/cost |
| `GET /switches/{name}/optics` | SFP presence + DDM (temp/voltage/bias/TX-RX mW & dBm) |
| `GET /switches/{name}/mirror` | port-mirror sessions |
| `GET /switches/{name}/firmware` | image/active-slot status |
| `GET /switches/{name}/users` | local accounts + privilege |
| `GET /switches/{name}/snmp` | community strings — SENSITIVE, treat as credentials |
| `GET /switches/{name}/raw?sections=a,b` | raw endpoint payloads |

Device command surface: see
[`docs/VIMIN_COMMAND_REFERENCE.md`](docs/VIMIN_COMMAND_REFERENCE.md)
(258 GET / 257 SET CGI commands, live-probed status, firmware quirks).

Auth: `Authorization: Bearer $CSP_API_TOKEN` on everything except
`/healthz`. If the token env var is unset, auth is disabled — reported
by `/healthz` (`auth_enabled: false`); acceptable only on loopback dev
runs.

Status codes: `404` unknown host · `502` switch unreachable/auth failed ·
`501` model not normalized yet (use `/raw`).

## Normalization coverage

| Model | Normalized | Fallback |
|---|---|---|
| `vm-s100-0800ms` (VIMIN) | ✅ thirteen resources — validated live against fw 3.5.0.10 | — |
| `sl-swtg124as`, `sl-swtgw218as` (Sodola) | ⏳ | `/raw` |
| `10g08-0800gsm` (Binardat) | ⏳ | `/raw` |

Adding a model = a set of pure functions in `csp_api/normalizers.py`
registered under its canonical key + a `RESOURCE_SECTIONS` entry in
`csp_api/pool.py` + a live-capture fixture in `tests/fixtures/`.

## Tests

```bash
.venv/Scripts/python -m pytest tests -q
```

`tests/fixtures/vimin33_raw.json` is a real capture from
`SW-TOR01-VIM10g` — normalizer assertions are contracts against
firmware quirks, not invented shapes. API tests stub the pool; no
network needed.
