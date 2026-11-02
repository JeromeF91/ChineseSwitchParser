"""FastAPI application — read-only normalized endpoints over the switch fleet.

Run (LAN-only by default — these switches hold admin creds, keep the API
off any inbound surface):

    set CSP_API_TOKEN=...   # required bearer token
    set CSP_HOSTS_FILE=hosts.yaml
    uvicorn csp_api.app:app --host 127.0.0.1 --port 8787
"""

from __future__ import annotations

import os
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:  # silence verify=False noise from the switch clients
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:  # pragma: no cover
    pass
warnings.filterwarnings("ignore", message=".*Unverified HTTPS request.*")

from fastapi import Depends, FastAPI, Header, HTTPException, Query  # noqa: E402

from .normalizers import NORMALIZERS, get_normalizer  # noqa: E402
from .pool import (  # noqa: E402
    RESOURCE_SECTIONS,
    RESOURCES,
    SwitchPool,
    SwitchUnavailable,
    UnsupportedModel,
)
from .registry import HostConfig, load_registry  # noqa: E402
from .schemas import HostSummary, ResourceResponse  # noqa: E402

API_TOKEN_ENV = "CSP_API_TOKEN"


def create_app(
    hosts_path: Optional[Path] = None,
    pool: Optional[Any] = None,
    registry: Optional[Dict[str, HostConfig]] = None,
) -> FastAPI:
    app = FastAPI(
        title="ChineseSwitchParser API",
        version="0.1.0",
        description="Read-only normalized switch data. Credentials live "
        "server-side in the host registry; callers use host names.",
    )
    app.state.registry = registry if registry is not None else load_registry(hosts_path)
    app.state.pool = pool or SwitchPool()

    def require_token(authorization: Optional[str] = Header(None)) -> None:
        token = os.environ.get(API_TOKEN_ENV)
        if not token:
            return  # auth disabled (dev); reported in /healthz
        if authorization != f"Bearer {token}":
            raise HTTPException(status_code=401, detail="missing or invalid bearer token")

    def get_host(name: str) -> HostConfig:
        cfg = app.state.registry.get(name)
        if cfg is None:
            raise HTTPException(
                status_code=404,
                detail=f"unknown host {name!r}; known: {sorted(app.state.registry)}",
            )
        return cfg

    def build_response(cfg: HostConfig, resource: str, data: Any, warnings_: list) -> ResourceResponse:
        return ResourceResponse(
            host=cfg.name,
            url=cfg.url,
            model=app.state.pool.model_key(cfg),
            fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            data=data,
            warnings=warnings_,
        )

    @app.get("/healthz")
    def healthz() -> Dict[str, Any]:
        return {
            "status": "ok",
            "auth_enabled": bool(os.environ.get(API_TOKEN_ENV)),
            "hosts": len(app.state.registry),
            "normalized_models": sorted(NORMALIZERS),
        }

    @app.get("/switches", response_model=list[HostSummary], dependencies=[Depends(require_token)])
    def list_switches() -> list[HostSummary]:
        return [
            HostSummary(name=c.name, url=c.url, model_configured=c.model)
            for c in app.state.registry.values()
        ]

    @app.get("/switches/{name}/detect", dependencies=[Depends(require_token)])
    def detect(name: str) -> Dict[str, Any]:
        cfg = get_host(name)
        try:
            return {"host": name, "model": app.state.pool.model_key(cfg)}
        except SwitchUnavailable as exc:
            raise HTTPException(status_code=502, detail=str(exc))

    def _normalized(name: str, resource: str) -> ResourceResponse:
        cfg = get_host(name)
        model_key = None
        try:
            model_key = app.state.pool.model_key(cfg)
            normalizer = get_normalizer(model_key, resource)
        except UnsupportedModel as exc:
            raise HTTPException(status_code=501, detail=str(exc))
        except SwitchUnavailable as exc:
            raise HTTPException(status_code=502, detail=str(exc))

        sections = RESOURCE_SECTIONS.get(model_key, {}).get(resource, [])
        if not sections:
            raise HTTPException(
                status_code=501,
                detail=f"resource {resource!r} not mapped for model {model_key!r}",
            )
        try:
            raw, warns = app.state.pool.fetch_raw(cfg, sections)
        except SwitchUnavailable as exc:
            raise HTTPException(status_code=502, detail=str(exc))
        return build_response(cfg, resource, normalizer(raw), warns)

    def _make_route(resource: str):
        def endpoint(name: str):
            return _normalized(name, resource)

        endpoint.__name__ = f"get_{resource}"
        return endpoint

    for _res in RESOURCES:
        app.add_api_route(
            f"/switches/{{name}}/{_res.replace('_', '-')}",
            _make_route(_res),
            methods=["GET"],
            tags=["switches"],
        )

    @app.get("/switches/{name}/raw", dependencies=[Depends(require_token)])
    def raw(name: str, sections: Optional[str] = Query(
        None, description="comma-separated endpoint keys; default: all for the model")) -> Dict[str, Any]:
        cfg = get_host(name)
        try:
            model_key = app.state.pool.model_key(cfg)
        except SwitchUnavailable as exc:
            raise HTTPException(status_code=502, detail=str(exc))
        client = app.state.pool.get_client(cfg)
        if sections:
            keys = [s.strip() for s in sections.split(",") if s.strip()]
        else:
            keys = list(client.api_endpoints)
        try:
            data, warns = app.state.pool.fetch_raw(cfg, keys)
        except SwitchUnavailable as exc:
            raise HTTPException(status_code=502, detail=str(exc))
        return {
            "host": name,
            "model": model_key,
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "data": data,
            "warnings": warns,
        }

    return app


# Module-level app for `uvicorn csp_api.app:app`. Requires a registry —
# refuse loudly at serve time rather than serving an empty fleet.
if os.environ.get("CSP_HOSTS_FILE") or Path("hosts.yaml").exists():
    app = create_app()
