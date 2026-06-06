"""
Browser MCP Server — playwright + mitmproxy para pentesting web
Expone tools de navegacion, interaccion con formularios, ejecucion de JS
y captura/intercepcion de trafico HTTP/S.
"""
import asyncio
import json
import os
import subprocess
from pathlib import Path

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn

AUDITS_DIR = Path("/audits")

# ── Browser state ──────────────────────────────────────────────
_playwright_ctx = None
_browser = None
_page = None
_request_log: list[dict] = []

# ── Proxy state ────────────────────────────────────────────────
_proxy_proc: subprocess.Popen | None = None
_flow_log_path = "/tmp/mitm_flows.jsonl"
_flow_logger_script = "/tmp/flow_logger.py"

# mitmproxy addon written to disk at proxy_start time
FLOW_LOGGER_CODE = '''\
import json
from mitmproxy import http

LOG_PATH = "/tmp/mitm_flows.jsonl"

def response(flow: http.HTTPFlow) -> None:
    try:
        entry = {
            "url": flow.request.pretty_url,
            "method": flow.request.method,
            "status_code": flow.response.status_code,
            "request_headers": dict(flow.request.headers),
            "request_body": (flow.request.get_text() or "")[:500],
            "response_headers": dict(flow.response.headers),
            "response_body": (flow.response.get_text() or "")[:500],
        }
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\\n")
    except Exception:
        pass
'''

server = Server("browser-mcp")


async def _get_or_create_page():
    """Return the persistent page, creating browser/context if needed."""
    global _playwright_ctx, _browser, _page
    from playwright.async_api import async_playwright

    if _playwright_ctx is None:
        _playwright_ctx = await async_playwright().start()
    if _browser is None or not _browser.is_connected():
        _browser = await _playwright_ctx.chromium.launch(headless=True)
        context = await _browser.new_context(ignore_https_errors=True)
        _page = await context.new_page()
        # Capture all responses for proxy_get_flows
        _page.on("response", lambda r: _request_log.append({
            "url": r.url,
            "method": r.request.method,
            "status_code": r.status,
        }))
    return _page


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="browser_navigate",
            description=(
                "Navegar a una URL con Playwright. "
                "Retorna titulo de pagina, status HTTP y screenshot opcional. "
                "Usar output_path para guardar evidencia visual del hallazgo."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL a navegar"},
                    "use_proxy": {
                        "type": "boolean",
                        "default": False,
                        "description": "Enrutar trafico por mitmproxy (requiere proxy_start previo)",
                    },
                    "proxy_port": {"type": "integer", "default": 8080},
                    "output_path": {
                        "type": "string",
                        "description": "Ruta relativa a /audits/ para screenshot (ej: evidence/F-001.png)",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="browser_screenshot",
            description="Capturar screenshot del estado actual de la pagina. Usar para evidencias de hallazgos.",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_path": {
                        "type": "string",
                        "description": "Ruta relativa a /audits/ (ej: evidence/F-003_xss.png)",
                    }
                },
                "required": ["output_path"],
            },
        ),
        Tool(
            name="browser_get_source",
            description="Obtener HTML fuente de la pagina actual.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="browser_fill",
            description="Llenar un campo de formulario por selector CSS.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "Selector CSS del campo"},
                    "value": {"type": "string", "description": "Valor a escribir"},
                },
                "required": ["selector", "value"],
            },
        ),
        Tool(
            name="browser_click",
            description="Hacer click en un elemento por selector CSS.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "Selector CSS del elemento"}
                },
                "required": ["selector"],
            },
        ),
        Tool(
            name="browser_eval_js",
            description=(
                "Ejecutar JavaScript en el contexto de la pagina. "
                "Util para testing de XSS (verificar ejecucion de payload), "
                "DOM-based vulnerabilities, y extraccion de datos del cliente."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {"type": "string", "description": "Codigo JavaScript a ejecutar"}
                },
                "required": ["script"],
            },
        ),
        Tool(
            name="proxy_start",
            description=(
                "Iniciar mitmproxy para interceptar y capturar trafico HTTP/S. "
                "Luego usar browser_navigate con use_proxy=true para enrutar el browser por el proxy."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "listen_port": {"type": "integer", "default": 8080, "description": "Puerto de escucha"}
                },
            },
        ),
        Tool(
            name="proxy_stop",
            description="Detener mitmproxy.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="proxy_get_flows",
            description=(
                "Obtener requests/responses capturados. "
                "Retorna playwright_flows (todas las pages navegadas) "
                "y proxy_flows (trafico interceptado por mitmproxy si esta activo)."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="proxy_clear_flows",
            description="Limpiar historial de flujos capturados (playwright + proxy).",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    global _browser, _page, _playwright_ctx, _proxy_proc, _request_log

    def ok(data: dict) -> list[TextContent]:
        return [TextContent(type="text", text=json.dumps({"success": True, **data}))]

    def err(msg: str) -> list[TextContent]:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": msg}))]

    try:
        # ── Browser tools ──────────────────────────────────────
        if name == "browser_navigate":
            url = arguments["url"]
            use_proxy = arguments.get("use_proxy", False)
            proxy_port = arguments.get("proxy_port", 8080)
            output_path = arguments.get("output_path")

            from playwright.async_api import async_playwright

            if use_proxy:
                if _playwright_ctx is None:
                    _playwright_ctx = await async_playwright().start()
                b = await _playwright_ctx.chromium.launch(
                    headless=True,
                    proxy={"server": f"http://localhost:{proxy_port}"},
                )
                ctx = await b.new_context(ignore_https_errors=True)
                p = await ctx.new_page()
            else:
                p = await _get_or_create_page()

            resp = await p.goto(url, wait_until="domcontentloaded", timeout=30000)
            status = resp.status if resp else None
            title = await p.title()

            screenshot_path = None
            if output_path:
                full = AUDITS_DIR / output_path
                full.parent.mkdir(parents=True, exist_ok=True)
                await p.screenshot(path=str(full), full_page=True)
                screenshot_path = str(full)

            if use_proxy:
                await b.close()
            else:
                _page = p

            return ok({"url": url, "status": status, "title": title, "screenshot_path": screenshot_path})

        elif name == "browser_screenshot":
            if _page is None:
                return err("No hay pagina activa. Usar browser_navigate primero.")
            output_path = arguments["output_path"]
            full = AUDITS_DIR / output_path
            full.parent.mkdir(parents=True, exist_ok=True)
            await _page.screenshot(path=str(full), full_page=True)
            return ok({"path": str(full), "size_bytes": full.stat().st_size})

        elif name == "browser_get_source":
            if _page is None:
                return err("No hay pagina activa.")
            return ok({"html": await _page.content()})

        elif name == "browser_fill":
            if _page is None:
                return err("No hay pagina activa.")
            await _page.fill(arguments["selector"], arguments["value"])
            return ok({"selector": arguments["selector"]})

        elif name == "browser_click":
            if _page is None:
                return err("No hay pagina activa.")
            await _page.click(arguments["selector"])
            return ok({"selector": arguments["selector"]})

        elif name == "browser_eval_js":
            if _page is None:
                return err("No hay pagina activa.")
            result = await _page.evaluate(arguments["script"])
            return ok({"result": result})

        # ── Proxy tools ────────────────────────────────────────
        elif name == "proxy_start":
            listen_port = arguments.get("listen_port", 8080)
            if _proxy_proc and _proxy_proc.poll() is None:
                return ok({
                    "message": "Proxy ya esta corriendo",
                    "upstream_proxy": f"http://localhost:{listen_port}",
                })
            # Write the flow logger addon script
            with open(_flow_logger_script, "w") as f:
                f.write(FLOW_LOGGER_CODE)
            # Clear existing flows file
            if os.path.exists(_flow_log_path):
                os.remove(_flow_log_path)
            # Start mitmdump with the addon
            _proxy_proc = subprocess.Popen(
                [
                    "mitmdump",
                    "--listen-port", str(listen_port),
                    "--ssl-insecure",
                    "--quiet",
                    "-s", _flow_logger_script,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            await asyncio.sleep(1.5)
            if _proxy_proc.poll() is not None:
                return err("No se pudo iniciar mitmproxy")
            return ok({
                "upstream_proxy": f"http://localhost:{listen_port}",
                "message": (
                    f"mitmproxy escuchando en puerto {listen_port}. "
                    "Usar browser_navigate con use_proxy=true para enrutar trafico."
                ),
            })

        elif name == "proxy_stop":
            if _proxy_proc and _proxy_proc.poll() is None:
                _proxy_proc.terminate()
                _proxy_proc = None
                return ok({"message": "Proxy detenido"})
            return ok({"message": "Proxy no estaba corriendo"})

        elif name == "proxy_get_flows":
            pw_flows = list(_request_log)
            mitm_flows: list[dict] = []
            if os.path.exists(_flow_log_path):
                with open(_flow_log_path) as f:
                    for line in f:
                        try:
                            mitm_flows.append(json.loads(line.strip()))
                        except Exception:
                            pass
            return ok({
                "playwright_flows": pw_flows,
                "proxy_flows": mitm_flows,
                "total": len(pw_flows) + len(mitm_flows),
            })

        elif name == "proxy_clear_flows":
            _request_log.clear()
            if os.path.exists(_flow_log_path):
                os.remove(_flow_log_path)
            return ok({"message": "Flujos limpiados"})

    except Exception as e:
        return err(str(e))

    return err(f"Tool desconocida: {name}")


def create_app() -> Starlette:
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )

    async def handle_health(request):
        return JSONResponse({"status": "ok", "service": "browser-mcp"})

    return Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
            Route("/health", endpoint=handle_health),
        ]
    )


if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=3478)
