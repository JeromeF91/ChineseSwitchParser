"""RTLPlayground firmware / httpd_sim.py device model.

RTLPlayground (https://github.com/logicog/RTLPlayground) is open firmware for
RTL8372/RTL8373 2.5G switches whose web API answers the same JSON contract as
the repo's tools/httpd_sim.py simulator, so this model serves both.

Auth contract (verified against firmware httpd/httpd.c run_login_body and
tools/httpd_sim.py, 2026-11-15): POST /login body "pwd=<password>" (no
username); success = 302 to index.html with a ``session=<token>`` cookie;
wrong password = 302 to login.html with no cookie. Unauthenticated API calls
return plain-text "Unauthorized".
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import BaseSwitchModel

logger = logging.getLogger(__name__)

# Endpoints whose responses are arrays plus an in-band cursor; fetch loops
# until the cursor wraps. l2.json entries carry "idx" (hex, hash-slot order)
# and the array truncates at the 8051 outbuf, so a single GET never returns
# the whole hardware table.
_CURSOR_ENDPOINTS = {"l2.json"}

# A cap guards against a wrap bug in the cursor walk.
_MAX_PAGES = 2000


class RTLPlayground(BaseSwitchModel):
    """Model for RTLPlayground-flashed switches (and the device simulator)."""

    def get_model_name(self) -> str:
        return "rtlplayground"

    def get_api_endpoints(self) -> Dict[str, str]:
        return {
            "info": "information.json",
            "ports": "ports.json",
            "traffic": "traffic.json",
            "vlans": "vlan.json",
            "vlanlist": "vlanlist.json",
            "mac_table": "l2.json",
            "lldp": "lldp.json",
            "stp": "stp.json",
            "mirror": "mirror.json",
            "lag": "lag.json",
            "eee": "eee.json",
            "isolation": "isolation.json",
            "bandwidth": "bandwidth.json",
            "storm": "storm.json",
            "counters": "counters.json",
        }

    def get_login_endpoint(self) -> str:
        return "login"

    # -- auth --------------------------------------------------------------

    def authenticate(self) -> bool:
        """POST the password; accept only when a session cookie came back
        (302 alone also happens on a wrong password, redirecting to
        login.html). A username is never sent — RTLPlayground has none."""
        try:
            resp = self.session.post(
                f"{self.url}/login",
                data={"pwd": self.password},
                allow_redirects=False,
                timeout=10,
            )
        except Exception as exc:  # noqa: BLE001 - embedded device, any failure
            logger.error("RTLPlayground login error at %s: %s", self.url, exc)
            return False
        cookie = self.session.cookies.get("session")
        if resp.status_code not in (200, 302) or not cookie:
            logger.warning(
                "RTLPlayground auth failed at %s (HTTP %s, cookie=%s)",
                self.url, resp.status_code, bool(cookie),
            )
            return False
        return True

    # -- fetch -------------------------------------------------------------

    def get_data(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """GET an endpoint; return one merged payload per section key.

        - l2.json: cursor-walked across pages into {"entries": [...]}
        - vlan.json: enumerated per VLAN (firmware answers one vid per GET;
          ids come from vlanlist.json) into {"entries": [{"vid", ...}]}
        - anything else: parsed body as-is.
        """
        base = endpoint.split("?")[0]
        if base in _CURSOR_ENDPOINTS:
            return self._fetch_paginated(base)
        if base == "vlan.json":
            return self._fetch_vlans()
        return super().get_data(endpoint)

    def _fetch_vlans(self) -> Optional[Dict[str, Any]]:
        vlist = super().get_data("vlanlist.json")
        if not isinstance(vlist, dict):
            return None
        entries: List[Dict[str, Any]] = []
        for meta in vlist.get("vlan", []):
            vid = meta.get("id")
            if vid is None:
                continue
            detail = super().get_data(f"vlan.json?vid={vid}")
            if isinstance(detail, dict):
                entries.append({"vid": vid, **detail})
        return {"entries": entries, "mgmt": vlist.get("mgmt")}

    def _fetch_paginated(self, base: str) -> Optional[Dict[str, Any]]:
        """Walk a cursor-paginated table to completion.

        Quirk (verified in firmware httpd/httpd.c and tools/httpd_sim.py,
        2026-11-15): the "idx" cursor is EMITTED as hex but PARSED as decimal
        (parse_short is digits-only; the sim's int(x, 0) even rejects
        zero-padded values and restarts at 0). So the returned cursor must be
        int(hex) + 1 and sent as a plain decimal string. "?idx=N" is
        inclusive of the entry at N — hence the +1 to avoid a duplicate row.
        """
        entries: List[Dict[str, Any]] = []
        idx: Optional[int] = None
        for _ in range(_MAX_PAGES):
            url = f"{self.url}/{base}" + (f"?idx={idx}" if idx else "")
            try:
                resp = self.session.get(url, timeout=10)
            except Exception as exc:  # noqa: BLE001
                logger.error("RTLPlayground %s fetch error: %s", base, exc)
                return None
            if resp.status_code != 200:
                logger.warning(
                    "RTLPlayground %s: HTTP %s", base, resp.status_code
                )
                return None
            try:
                page = resp.json()
            except ValueError:
                logger.warning("RTLPlayground %s: non-JSON body", base)
                return None
            if not isinstance(page, list) or not page:
                break
            entries.extend(page)
            cursor = page[-1].get("idx")
            if cursor is None:
                break
            try:
                nxt = int(str(cursor), 16) + 1  # hex out, decimal in
            except ValueError:
                logger.warning(
                    "RTLPlayground %s: unparseable idx cursor %r", base, cursor
                )
                break
            if idx is not None and nxt <= idx:
                break  # cursor not advancing — stop rather than spin
            idx = nxt
        else:
            logger.warning(
                "RTLPlayground %s: page cap hit after %d entries", base, len(entries)
            )
        return {"entries": entries}
