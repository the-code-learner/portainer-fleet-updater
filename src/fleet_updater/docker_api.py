from __future__ import annotations

import http.client
import json
import socket


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: str) -> None:
        super().__init__("localhost")
        self.socket_path = socket_path

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.socket_path)
        self.sock = sock


class DockerAPI:
    def __init__(self, socket_path: str = "/var/run/docker.sock") -> None:
        self.socket_path = socket_path

    def get_json(self, path: str):
        conn = UnixHTTPConnection(self.socket_path)
        try:
            conn.request("GET", path)
            response = conn.getresponse()
            body = response.read()
            if not 200 <= response.status < 300:
                raise RuntimeError(
                    f"Docker API HTTP {response.status}: "
                    f"{body.decode('utf-8', 'replace')[:500]}"
                )
            return json.loads(body) if body else None
        finally:
            conn.close()

    def detect_local_portainer(self, forced_url: str = "") -> dict:
        containers = self.get_json("/containers/json?all=1") or []
        candidates = []
        for container in containers:
            image = str(container.get("Image") or "").lower()
            names = [str(x).lstrip("/").lower() for x in container.get("Names") or []]
            if (
                image.startswith("portainer/portainer-ce")
                or image.startswith("portainer/portainer-ee")
                or "portainer" in names
            ):
                candidates.append(container)

        if not candidates:
            if forced_url:
                return {
                    "container_id": None,
                    "container_name": None,
                    "image": None,
                    "api_url": forced_url.rstrip("/"),
                    "auto_detected": False,
                }
            raise RuntimeError(
                "Portainer container not found on the local Docker host. "
                "Set PORTAINER_URL explicitly."
            )

        container = candidates[0]
        inspect = self.get_json(f"/containers/{container['Id']}/json") or {}
        config = inspect.get("Config") or {}
        network = inspect.get("NetworkSettings") or {}
        ports = network.get("Ports") or {}

        api_url = forced_url.rstrip("/") if forced_url else ""
        if not api_url:
            for container_port, scheme in (("9443/tcp", "https"), ("9000/tcp", "http")):
                bindings = ports.get(container_port) or []
                if bindings and bindings[0].get("HostPort"):
                    api_url = f"{scheme}://host.docker.internal:{bindings[0]['HostPort']}"
                    break

        if not api_url:
            raise RuntimeError(
                "Portainer was detected locally, but no published 9443/9000 port was found. "
                "Set PORTAINER_URL explicitly."
            )

        return {
            "container_id": str(container.get("Id") or "")[:12],
            "container_name": str(inspect.get("Name") or "").lstrip("/") or "portainer",
            "image": config.get("Image") or container.get("Image"),
            "api_url": api_url,
            "auto_detected": not bool(forced_url),
        }
