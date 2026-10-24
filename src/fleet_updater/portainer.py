from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request


class PortainerClient:
    def __init__(self, base_url: str, api_token: str, verify_tls: bool = False) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token.strip()
        self.verify_tls = verify_tls

    def _context(self):
        if self.base_url.lower().startswith("https://") and not self.verify_tls:
            return ssl._create_unverified_context()
        return None

    def get_json(self, path: str):
        request = urllib.request.Request(
            self.base_url + path,
            headers={
                "Accept": "application/json",
                "X-API-Key": self.api_token,
                "User-Agent": "Portainer-Fleet-Updater",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=15, context=self._context()) as response:
                body = response.read()
                return json.loads(body) if body else None
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:1000]
            if exc.code in (401, 403):
                raise RuntimeError(
                    f"Portainer token rejected or insufficient permissions (HTTP {exc.code})."
                ) from exc
            raise RuntimeError(f"Portainer HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Cannot reach Portainer: {exc.reason}") from exc

    def status(self) -> dict:
        value = self.get_json("/api/status")
        return value if isinstance(value, dict) else {}

    def endpoints(self) -> list[dict]:
        value = self.get_json("/api/endpoints")
        if not isinstance(value, list):
            raise RuntimeError("Unexpected response from /api/endpoints")
        return value

    def stacks(self) -> list[dict]:
        value = self.get_json("/api/stacks")
        if not isinstance(value, list):
            raise RuntimeError("Unexpected response from /api/stacks")
        return value


def reported_agent_version(endpoint: dict) -> str | None:
    agent = endpoint.get("Agent")
    if isinstance(agent, dict) and agent.get("Version"):
        return str(agent["Version"])
    for key in ("AgentVersion", "EdgeAgentVersion"):
        if endpoint.get(key):
            return str(endpoint[key])
    return None
