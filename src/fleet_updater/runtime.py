from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import __version__
from .docker_api import DockerAPI
from .portainer import PortainerClient, reported_agent_version
from .state import SettingsStore

HOST = os.environ.get("PFU_HOST", "0.0.0.0")
PORT = int(os.environ.get("PFU_PORT", "8080"))
FORCED_PORTAINER_URL = os.environ.get("PORTAINER_URL", "").strip()
PORTAINER_API_TOKEN = (
    os.environ.get("PORTAINER_API_TOKEN")
    or os.environ.get("PORTAINER_TOKEN")
    or ""
).strip()
VERIFY_TLS = os.environ.get("PORTAINER_VERIFY_TLS", "false").lower() in {
    "1", "true", "yes", "on"
}

store = SettingsStore()
docker = DockerAPI()


def scan() -> dict:
    if not PORTAINER_API_TOKEN:
        raise RuntimeError(
            "PORTAINER_API_TOKEN is not configured. Create an Access Token in Portainer "
            "and set it only in your private Portainer stack."
        )

    local = docker.detect_local_portainer(FORCED_PORTAINER_URL)
    client = PortainerClient(local["api_url"], PORTAINER_API_TOKEN, verify_tls=VERIFY_TLS)
    status = client.status()
    endpoints = client.endpoints()
    stacks = client.stacks()
    managed = store.managed_stack_ids()

    endpoint_map: dict[int, dict] = {}
    environment_rows = []
    for endpoint in endpoints:
        try:
            endpoint_id = int(endpoint.get("Id"))
        except (TypeError, ValueError):
            continue
        endpoint_map[endpoint_id] = endpoint
        environment_rows.append(
            {
                "id": endpoint_id,
                "name": endpoint.get("Name") or f"Endpoint {endpoint_id}",
                "url": endpoint.get("URL") or "",
                "type": endpoint.get("Type"),
                "status": endpoint.get("Status"),
                "agent_version": reported_agent_version(endpoint),
            }
        )

    stack_rows = []
    for stack in stacks:
        try:
            stack_id = int(stack.get("Id"))
        except (TypeError, ValueError):
            continue
        try:
            endpoint_id = int(stack.get("EndpointId"))
        except (TypeError, ValueError):
            endpoint_id = 0
        endpoint = endpoint_map.get(endpoint_id) or {}
        stack_rows.append(
            {
                "id": stack_id,
                "name": stack.get("Name") or f"Stack {stack_id}",
                "endpoint_id": endpoint_id,
                "environment": endpoint.get("Name") or f"Endpoint {endpoint_id}",
                "type": stack.get("Type"),
                "status": stack.get("Status"),
                "managed": stack_id in managed,
            }
        )

    stack_rows.sort(key=lambda item: (str(item["environment"]).lower(), str(item["name"]).lower()))
    environment_rows.sort(key=lambda item: str(item["name"]).lower())

    return {
        "app": {"version": __version__},
        "portainer": {
            **local,
            "version": status.get("Version") or status.get("version") or "unknown",
        },
        "environments": environment_rows,
        "stacks": stack_rows,
    }


INDEX = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Portainer Fleet Updater</title>
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#121a2d;--panel2:#182239;--text:#eef3ff;--muted:#93a4c3;--line:#273653;--ok:#4ade80;--warn:#fbbf24}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.45 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:1180px;margin:auto;padding:30px 20px 60px}header{display:flex;gap:18px;align-items:flex-start;justify-content:space-between;margin-bottom:22px}
h1{margin:0 0 5px;font-size:26px}h2{font-size:16px;margin:0 0 14px}.muted{color:var(--muted)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:18px}.notice{padding:12px 14px;border:1px solid #29446e;background:#14213a;border-radius:10px;margin-bottom:18px}
#error{display:none;background:#35131d;border-color:#6b2135;color:#fecdd3}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}
.metric{background:var(--panel2);padding:12px;border-radius:10px}.metric b{display:block;margin-top:4px;overflow-wrap:anywhere}
button{border:1px solid #3b82f6;background:#2563eb;color:#fff;padding:9px 14px;border-radius:9px;font-weight:700;cursor:pointer}button:disabled{opacity:.55;cursor:wait}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:10px 9px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.pill{display:inline-block;padding:3px 8px;border-radius:999px;font-size:12px;font-weight:700}.ok{color:var(--ok);background:#123020}.warn{color:var(--warn);background:#352a0d}
.actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.tablewrap{overflow:auto}input[type=checkbox]{width:18px;height:18px}
@media(max-width:760px){header{flex-direction:column}table{min-width:760px}}
</style>
</head>
<body><main>
<header><div><h1>Portainer Fleet Updater</h1><div class="muted">v<span id="appVersion">…</span> · safe discovery baseline</div></div><button id="refresh" onclick="loadData()">Scan</button></header>
<div class="notice">v0.1.0 is intentionally non-destructive: it discovers Portainer, environments and stacks. Managed-stack checkboxes are stored only in Fleet Updater's own <code>/data</code> volume.</div>
<div id="error" class="notice"></div>
<section class="card"><h2>Portainer Server</h2><div id="server" class="grid"><div class="muted">Scanning…</div></div></section>
<section class="card"><h2>Environments</h2><div class="tablewrap"><table><thead><tr><th>Name</th><th>URL</th><th>Agent version</th><th>Status</th></tr></thead><tbody id="envRows"><tr><td colspan="4" class="muted">Scanning…</td></tr></tbody></table></div></section>
<section class="card">
<div class="actions" style="justify-content:space-between;margin-bottom:10px"><div><h2 style="margin:0">Stacks</h2><div class="muted">Tick the stacks Fleet Updater should manage in future releases.</div></div><div class="actions"><button onclick="selectAll(true)">Select all</button><button onclick="selectAll(false)">Select none</button><button id="save" onclick="saveManaged()">Save selection</button></div></div>
<div class="tablewrap"><table><thead><tr><th>Managed</th><th>Environment</th><th>Stack</th><th>Type</th><th>Status</th></tr></thead><tbody id="stackRows"><tr><td colspan="5" class="muted">Scanning…</td></tr></tbody></table></div>
</section>
</main>
<script>
function esc(v){return String(v??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;")}
function metric(k,v){return '<div class="metric"><span class="muted">'+esc(k)+'</span><b>'+esc(v)+'</b></div>'}
function selectAll(value){document.querySelectorAll('.managed').forEach(x=>x.checked=value)}
function showError(msg){const e=document.getElementById("error");e.textContent=msg;e.style.display="block"}
async function saveManaged(){const btn=document.getElementById("save");btn.disabled=true;try{const ids=[...document.querySelectorAll('.managed:checked')].map(x=>Number(x.dataset.id));const r=await fetch("/api/managed-stacks",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ids})});const d=await r.json();if(!r.ok)throw new Error(d.error||"Save failed");await loadData()}catch(e){showError(e.message)}finally{btn.disabled=false}}
async function loadData(){const btn=document.getElementById("refresh");btn.disabled=true;document.getElementById("error").style.display="none";try{const r=await fetch("/api/scan",{cache:"no-store"});const d=await r.json();if(!r.ok)throw new Error(d.error||"Scan failed");document.getElementById("appVersion").textContent=d.app.version;const p=d.portainer;document.getElementById("server").innerHTML=metric("Container",p.container_name||"—")+metric("Image",p.image||"—")+metric("Portainer",p.version)+metric("API",p.api_url);document.getElementById("envRows").innerHTML=d.environments.map(e=>'<tr><td><b>'+esc(e.name)+'</b></td><td>'+esc(e.url||"—")+'</td><td>'+esc(e.agent_version||"—")+'</td><td><span class="pill '+(e.status===1?'ok':'warn')+'">'+esc(e.status===1?"online":"status "+e.status)+'</span></td></tr>').join("")||'<tr><td colspan="4" class="muted">No environments found.</td></tr>';document.getElementById("stackRows").innerHTML=d.stacks.map(s=>'<tr><td><input class="managed" type="checkbox" data-id="'+s.id+'" '+(s.managed?'checked':'')+'></td><td>'+esc(s.environment)+'</td><td><b>'+esc(s.name)+'</b><br><span class="muted">ID '+s.id+'</span></td><td>'+esc(s.type??"—")+'</td><td>'+esc(s.status??"—")+'</td></tr>').join("")||'<tr><td colspan="5" class="muted">No stacks found.</td></tr>'}catch(e){showError(e.message)}finally{btn.disabled=false}}
loadData();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    server_version = "PortainerFleetUpdater/" + __version__

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} - {fmt % args}", flush=True)

    def send_payload(self, status: int, payload: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(payload)

    def send_json(self, status: int, value) -> None:
        self.send_payload(status, json.dumps(value).encode(), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.send_payload(200, b"ok\n", "text/plain; charset=utf-8")
            return
        if self.path == "/":
            self.send_payload(200, INDEX.encode(), "text/html; charset=utf-8")
            return
        if self.path == "/api/scan":
            try:
                self.send_json(200, scan())
            except Exception as exc:
                self.send_json(500, {"error": str(exc)})
            return
        if self.path == "/api/managed-stacks":
            self.send_json(200, {"ids": sorted(store.managed_stack_ids())})
            return
        self.send_payload(404, b"not found\n", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        if self.path != "/api/managed-stacks":
            self.send_payload(404, b"not found\n", "text/plain; charset=utf-8")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 65536:
                raise ValueError("payload too large")
            payload = json.loads(self.rfile.read(length) or b"{}")
            ids = payload.get("ids")
            if not isinstance(ids, list):
                raise ValueError("ids must be a list")
            saved = store.set_managed_stack_ids([int(item) for item in ids])
            self.send_json(200, {"ids": saved})
        except Exception as exc:
            self.send_json(400, {"error": str(exc)})


def main() -> None:
    print(f"Portainer Fleet Updater v{__version__} listening on {HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
