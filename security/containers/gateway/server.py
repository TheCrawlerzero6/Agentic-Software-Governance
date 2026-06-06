"""
Gateway de Pentesting — MCP Streamable HTTP Server (100% local, sin autenticación)
Registra auditorías de seguridad en una MongoDB local. Pensado para correr en el
equipo del propio desarrollador junto con los contenedores kali y browser.

Modelo de datos: esquema rico (enums MAYUSCULA).
Ver los esquemas de referencia del proyecto en: reference/schema/*.md
  - audit_runs : audit_type (APROBACION_ACTIVOS | RETEST_APROBACION), checkpoint,
                 retest (parent_audit_id/retest_number), dictamen, report_sha256.
  - findings   : status (OPEN/FIXED/...) + analyst_review + dynamic_validation +
                 triage + retest_status + parent_finding_id.
  - events     : event_type en MAYUSCULA.
  - llm_attack_sessions : sesiones de ataque a chatbots/LLM.

Autenticación:
- AUTH_MODE=local (default): NO hay autenticación. La identidad/owner es un valor fijo
  configurable (AUDIT_OWNER, por defecto "local"). Todo corre en la máquina del usuario.
- AUTH_MODE=bearer: modo opcional con token Bearer para tests.

Telemetría:
- Cada operación relevante emite un doc en la colección `events` (event_type discriminator).
- Las invocaciones a tools Kali/browser se pueden enviar por HTTP a /tool-calls y se
  guardan en la colección `tool_calls` (opcional).
- Rechazos (scope) se loguean automáticamente como eventos.
"""

import os
import base64
import ipaddress
import json
import logging
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

import yaml
import pymongo
import pymongo.errors
from mcp.server import Server as McpServer
from mcp.types import Tool, TextContent
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pentest-gateway")

# --- Configuration ---


def load_config():
    config_path = os.environ.get("CONFIG_PATH", "config.yml")
    if os.path.exists(config_path):
        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = {}

    cfg.setdefault("mongodb", {})
    cfg["mongodb"].setdefault(
        "uri", os.environ.get("MONGODB_URI", "mongodb://localhost:27017/pentest_audits")
    )
    cfg["mongodb"].setdefault(
        "database", os.environ.get("MONGODB_DATABASE", "pentest_audits")
    )

    cfg.setdefault("auth", {})
    cfg["auth"].setdefault("mode", os.environ.get("AUTH_MODE", "local"))
    cfg["auth"].setdefault(
        "identity_header", os.environ.get("IDENTITY_HEADER", "X-Consumer-Username")
    )
    cfg["auth"].setdefault("api_key", os.environ.get("GATEWAY_API_KEY", ""))
    cfg["auth"].setdefault(
        "audit_owner", os.environ.get("AUDIT_OWNER", "local")
    )

    cfg.setdefault("server", {})
    cfg["server"].setdefault("host", "0.0.0.0")
    cfg["server"].setdefault("port", int(os.environ.get("GATEWAY_PORT", "3480")))
    cfg["server"].setdefault(
        "public_path_prefix",
        os.environ.get("PUBLIC_PATH_PREFIX", ""),
    )
    # 0 = sin límite (recomendado en local). >0 limita auditorías/día por owner.
    cfg["server"].setdefault(
        "daily_audit_limit",
        int(os.environ.get("DAILY_AUDIT_LIMIT", "0")),
    )
    # Por defecto solo localhost + redes privadas (RFC1918). Añade dominios extra
    # separados por coma vía ALLOWED_TARGET_DOMAINS si auditas hosts internos por nombre.
    cfg["server"].setdefault(
        "allowed_target_domains",
        os.environ.get("ALLOWED_TARGET_DOMAINS", ""),
    )

    return cfg


CONFIG = load_config()
PREFIX = CONFIG["server"]["public_path_prefix"].rstrip("/")
AUTH_MODE = CONFIG["auth"]["mode"]
AUDIT_OWNER = CONFIG["auth"]["audit_owner"]
IDENTITY_HEADER = CONFIG["auth"]["identity_header"].lower()
DAILY_AUDIT_LIMIT = int(CONFIG["server"]["daily_audit_limit"])

_raw_domains = CONFIG["server"]["allowed_target_domains"]
if isinstance(_raw_domains, list):
    ALLOWED_DOMAIN_SUFFIXES = [d.strip().lower().lstrip(".") for d in _raw_domains if d]
else:
    ALLOWED_DOMAIN_SUFFIXES = [
        d.strip().lower().lstrip(".")
        for d in str(_raw_domains).split(",")
        if d.strip()
    ]
ALLOWED_LOCAL_HOSTNAMES = {"localhost", "host.docker.internal"}
PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]

# --- Enums del modelo rico (MAYUSCULA) ---

VALID_AUDIT_TYPES = {"APROBACION_ACTIVOS", "RETEST_APROBACION"}
VALID_ASSET_TYPES = {"api", "web", "web_api", "chatbot", "n8n_flujo", "node_n8n"}
VALID_MODALITIES = {"WHITE_BOX", "GRAY_BOX", "BLACK_BOX", "MIXED"}
VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
VALID_CONFIDENCE = {"confirmed", "high", "medium", "low", "suspected"}
VALID_FINDING_STATUS = {
    "OPEN", "POTENTIAL", "INFORMATIONAL", "IN_REVIEW", "ACCEPTED_RISK",
    "FIXED", "PARTIAL_FIX", "WONT_FIX", "FALSE_POSITIVE", "REOPENED",
}
VALID_ANALYST_DECISIONS = {"CONFIRMED", "OUT_OF_SCOPE", "FALSE_POSITIVE", "DOWNGRADE", "PENDING"}
VALID_RETEST_STATUS = {"FIXED", "PARTIAL", "UNFIXED", "REGRESSED"}
VALID_TOOL_SERVERS = {"KALI", "BROWSER"}

# Estados de cierre que EXIGEN una nota (review_note) de >= 10 chars.
CLOSING_STATUSES_REQUIRING_NOTE = {"FIXED", "FALSE_POSITIVE", "WONT_FIX", "ACCEPTED_RISK"}

# Estados de finding que cuentan como "sin resolver" para dictamen / verify.
UNRESOLVED_STATUSES = {"OPEN", "POTENTIAL", "IN_REVIEW", "REOPENED"}

# event_types canónicos (deben coincidir con reference/schema/event.md). Un event_type
# fuera de esta lista se inserta con deprecated_schema=true (telemetría vieja/experimental).
CANONICAL_EVENT_TYPES = {
    "SKILL_INVOKED", "FLOW_BRANCH",
    "AUDIT_STARTED", "AUDIT_COMPLETED", "AUDIT_FAILED", "AUDIT_PAUSED", "AUDIT_RESUMED",
    "CHECKPOINT_UPDATED", "FINDING_DISCOVERED", "FINDING_REVIEWED",
    "TRIAGE_COMPLETED", "REPORT_GENERATED",
    "SCOPE_REJECTED", "RATE_LIMIT_HIT", "AUTH_FAILED",
    "TOOL_CALL", "ERROR",
}

# --- MongoDB ---

mongo_client = pymongo.MongoClient(CONFIG["mongodb"]["uri"])
db = mongo_client[CONFIG["mongodb"]["database"]]

# --- MongoDB Indexes ---

db.audit_runs.create_index("audit_id", unique=True)
db.audit_runs.create_index([("created_at", -1)])
db.audit_runs.create_index([("owner", 1), ("created_at", -1)])
db.audit_runs.create_index([("parent_audit_id", 1)])
db.findings.create_index("audit_id")
db.findings.create_index([("audit_id", 1), ("cvss_score", -1)])
db.findings.create_index("finding_id", unique=True)
db.findings.create_index([("owner", 1), ("status", 1)])
db.findings.create_index([("parent_finding_id", 1)])
db.events.create_index("audit_id")
db.events.create_index([("event_type", 1), ("timestamp", -1)])
db.events.create_index([("owner", 1), ("timestamp", -1)])
db.tool_calls.create_index([("owner", 1), ("timestamp", -1)])
db.tool_calls.create_index([("audit_id", 1), ("timestamp", 1)])
db.tool_calls.create_index([("tool_name", 1), ("timestamp", -1)])
db.llm_attack_sessions.create_index("session_id", unique=True)
db.llm_attack_sessions.create_index([("audit_id", 1), ("status", 1)])


# --- Request context ---

_identity_ctx: ContextVar[str] = ContextVar("identity", default="")
_client_ip_ctx: ContextVar[str] = ContextVar("client_ip", default="")
_performed_by_ctx: ContextVar[dict] = ContextVar("performed_by", default={})


def current_identity() -> str:
    return _identity_ctx.get()


def current_client_ip() -> str:
    return _client_ip_ctx.get()


def current_performed_by() -> dict:
    return _performed_by_ctx.get()


def current_department() -> str:
    return (_performed_by_ctx.get() or {}).get("department", "")


# --- Helpers ---


def _now():
    # UTC por defecto. Cambia TZ_OFFSET_HOURS (entero) si prefieres hora local.
    try:
        offset = int(os.environ.get("TZ_OFFSET_HOURS", "0"))
    except ValueError:
        offset = 0
    return datetime.now(timezone(timedelta(hours=offset)))


def _iso_now():
    return _now().isoformat()


def _today_start_iso():
    n = _now()
    return n.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()


def _seconds_until_midnight():
    n = _now()
    midnight = n.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return int((midnight - n).total_seconds())


def _extract_client_ip(request) -> str:
    xff = request.headers.get("x-forwarded-for", "").strip()
    if xff:
        return xff.split(",")[0].strip()
    client = getattr(request, "client", None)
    return client.host if client and hasattr(client, "host") else ""


def _decode_jwt_claims(authorization: str) -> dict:
    """Decodifica (sin verificar firma) el payload del JWT del API key. Kong ya validó la
    firma antes de reenviarlo, así que aquí solo extraemos claims para trazabilidad."""
    try:
        if not authorization:
            return {}
        token = authorization.split(" ", 1)[1] if " " in authorization else authorization
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        payload = parts[1] + "=" * (-len(parts[1]) % 4)  # padding base64url
        data = json.loads(base64.urlsafe_b64decode(payload))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _build_performed_by(request) -> dict:
    """Identidad de quien hace la operación. En modo local es un único usuario fijo
    (AUDIT_OWNER); el resto de campos quedan vacíos por compatibilidad con el esquema."""
    return {
        "user": AUDIT_OWNER,
        "custom_id": "",
        "consumer_id": "",
        "credential_id": "",
        "department": "",
        "purpose": "",
        "key_issued_at": None,
        "key_expires_at": None,
        "client_ip": _extract_client_ip(request),
        "auth_via": AUTH_MODE,
    }


def _log_event(event_type: str, *, audit_id: str | None = None,
               message: str = "", level_log: str = "INFO",
               context: dict | None = None, owner: str | None = None,
               client_ip: str | None = None) -> None:
    """Escribe un doc en la colección events. event_type va en MAYUSCULA. Falla silencioso
    (no rompe la tool). Un event_type fuera del set canónico se marca deprecated_schema."""
    doc_owner = owner if owner is not None else current_identity()
    doc_ip = client_ip if client_ip is not None else current_client_ip()
    doc_ctx = dict(context or {})
    doc_ctx.setdefault("source", "developer_plugin")
    doc_ctx.setdefault("owner", doc_owner)
    doc_ctx.setdefault("client_ip", doc_ip)
    doc = {
        "audit_id": audit_id,
        "owner": doc_owner,
        "department": current_department(),
        "timestamp": _iso_now(),
        "event_type": event_type,
        "message": message,
        "level_log": level_log,
        "context": doc_ctx,
    }
    if event_type not in CANONICAL_EVENT_TYPES:
        doc["deprecated_schema"] = True
    try:
        db.events.insert_one(doc)
    except Exception as e:
        logger.warning(f"No se pudo escribir evento {event_type}: {e}")


def _unauthorized(msg: str):
    return [TextContent(type="text", text=json.dumps({"success": False, "error": msg}))]


def _err(error_code: str, message: str, **extra):
    payload = {"success": False, "error_code": error_code, "error": message, **extra}
    return [TextContent(type="text", text=json.dumps(payload))]


def _is_validation_error(e: Exception) -> bool:
    """True si la excepción es un rechazo del validador $jsonSchema de MongoDB (code 121)."""
    code = getattr(e, "code", None)
    if code == 121:
        return True
    return "document failed validation" in str(e).lower()


def _validation_err(e: Exception):
    """Respuesta clara al LLM cuando MongoDB rechaza el documento por el validador.
    Permite que el cliente corrija los campos/enums y reintente."""
    detail = ""
    info = getattr(e, "details", None)
    if isinstance(info, dict):
        # Mongo entrega el detalle de qué regla falló en errInfo.details
        err_info = info.get("errInfo") or {}
        detail = json.dumps(err_info.get("details", err_info))[:600]
    if not detail:
        detail = str(e)[:600]
    return _err(
        "schema_validation_failed",
        ("El documento no cumple el esquema de la base (validación MongoDB $jsonSchema). "
         "Revisa los campos requeridos y que los enums estén en MAYÚSCULA. Corrige y reintenta."),
        detail=detail,
    )


def _validate_target_url(url: str) -> tuple[bool, str]:
    if not url:
        return False, "target_url vacío"

    parsed = urlparse(url if "://" in url else f"http://{url}")
    host = (parsed.hostname or "").lower()
    if not host:
        return False, f"target_url sin host: {url}"

    try:
        ip = ipaddress.ip_address(host)
        for net in PRIVATE_NETWORKS:
            if ip in net:
                return True, ""
        return False, (
            f"IP pública no permitida: {host}. Solo loopback (127.0.0.0/8) "
            "o RFC1918 (10/8, 172.16/12, 192.168/16)."
        )
    except ValueError:
        pass

    if host in ALLOWED_LOCAL_HOSTNAMES:
        return True, ""

    for suffix in ALLOWED_DOMAIN_SUFFIXES:
        if host == suffix or host.endswith("." + suffix):
            return True, ""

    return False, (
        f"target_url fuera de alcance: {host}. Solo se permite localhost, "
        f"host.docker.internal, redes privadas (RFC1918), o dominios: "
        f"{', '.join(ALLOWED_DOMAIN_SUFFIXES)}."
    )


def _compute_dictamen(audit_id: str) -> tuple[str, str | None]:
    """Calcula el dictamen de Aprobacion de Activos.

    Premisa: el dev debe dejar TODOS los findings en estado terminal (mitigado o
    justificado). El dictamen se deriva por buckets, sobre TODAS las severidades:

      - pendiente   : cualquier estado no terminal (OPEN/sin clasificar, confirmada sin
                      corregir, PARTIAL_FIX, etc.). Cualquier severidad. -> NO SE APRUEBA.
      - bloqueado   : CRITICAL/HIGH marcado FALSE_POSITIVE. Un crit/alto tiene impacto
                      demostrado (politica de severidad honesta), no puede ser
                      'comportamiento normal'. -> NO SE APRUEBA (+ revisar con seguridad).
      - condicion   : ACCEPTED_RISK o WONT_FIX (fuera de alcance). Riesgo justificado. -> CON CONDICIONES.
      - limpio      : FIXED, o FALSE_POSITIVE de baja/media/info.

    Nota: el plugin (review-loop) ya impide marcar FP/fuera-de-alcance un crit/alto de
    codigo propio; este calculo es el backstop a nivel servidor.
    """
    findings = list(db.findings.find({"audit_id": audit_id}))
    pending, blocked, conditions = [], [], []
    for f in findings:
        sev = (f.get("severity") or "").upper()
        status = (f.get("status") or "").upper()
        did = f.get("display_id")
        # Backstop retest: un hijo verificado FIXED en el retest cuenta como mitigado aunque
        # el plugin no lo haya cerrado (submit_finding crea con status=OPEN por defecto).
        if (f.get("retest_status") or "").upper() == "FIXED":
            continue
        if status == "FALSE_POSITIVE":
            if sev in ("CRITICAL", "HIGH"):
                blocked.append(did)        # crit/alto demostrado no puede ser falso positivo
            continue                       # FP de baja/media = descartado limpio
        if status == "FIXED":
            continue                       # mitigado
        if status in ("ACCEPTED_RISK", "WONT_FIX"):
            conditions.append(did)         # riesgo aceptado / fuera de alcance
            continue
        pending.append(did)                # OPEN, PARTIAL_FIX, REOPENED, ... = sin resolver

    if pending:
        ids = ", ".join(x for x in pending if x)
        return ("NO SE APRUEBA",
                f"Quedan vulnerabilidades sin resolver ni clasificar: {ids}. Debes "
                f"mitigarlas o justificarlas (falso positivo / aceptacion de riesgo / "
                f"fuera de alcance) antes de poder aprobar.")
    if blocked:
        ids = ", ".join(x for x in blocked if x)
        return ("NO SE APRUEBA",
                f"Vulnerabilidades CRITICAS/ALTAS marcadas como falso positivo pese a "
                f"tener impacto demostrado: {ids}. No pueden descartarse asi: corrigelas, "
                f"acepta formalmente el riesgo, o consulta con tu equipo de seguridad.")
    if conditions:
        ids = ", ".join(x for x in conditions if x)
        return ("SE APRUEBA CON CONDICIONES",
                f"Vulnerabilidades reales justificadas (riesgo aceptado / fuera de alcance): {ids}.")
    return "SE APRUEBA", None


def _compute_retest_comparison(audit_id: str, parent_audit_id: str | None) -> dict:
    """Cuenta los findings del retest por retest_status."""
    findings = list(db.findings.find({"audit_id": audit_id}))
    fixed = partial = unfixed = new = 0
    fixed_ids, unfixed_ids = [], []
    for f in findings:
        rs = f.get("retest_status")
        if f.get("parent_finding_id") is None:
            new += 1
        if rs == "FIXED":
            fixed += 1
            if f.get("display_id"):
                fixed_ids.append(f["display_id"])
        elif rs == "PARTIAL":
            partial += 1
        elif rs in ("UNFIXED", "REGRESSED"):
            unfixed += 1
            if f.get("display_id"):
                unfixed_ids.append(f["display_id"])

    if fixed > unfixed + new:
        direction = "MEJORANDO"
    elif fixed == unfixed + new:
        direction = "ESTABLE"
    else:
        direction = "EMPEORANDO"

    return {
        "original_audit_id": parent_audit_id,
        "fixed": fixed,
        "partial": partial,
        "unfixed": unfixed,
        "new": new,
        "risk_direction": direction,
        "fixed_ids": fixed_ids,
        "unfixed_ids": unfixed_ids,
    }


# --- MCP Server ---

mcp = McpServer("gateway")


@mcp.list_tools()
async def list_tools():
    return [
        Tool(
            name="submit_audit",
            description=(
                "Registrar el inicio de una nueva auditoría. audit_type por defecto "
                "APROBACION_ACTIVOS; para retest usar RETEST_APROBACION con parent_audit_id."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "asset_name": {"type": "string"},
                    "asset_type": {"type": "string", "enum": sorted(VALID_ASSET_TYPES)},
                    "target_url": {"type": "string"},
                    "audit_type": {"type": "string", "enum": sorted(VALID_AUDIT_TYPES)},
                    "modality": {"type": "string", "enum": sorted(VALID_MODALITIES)},
                    "docker_container": {"type": "string"},
                    "docker_image": {"type": "string"},
                    "source_code_path": {"type": "string"},
                    "language": {"type": "string"},
                    "framework": {"type": "string"},
                    "repository_url": {"type": "string"},
                    "has_auth": {"type": "boolean"},
                    "project_name": {"type": "string"},
                    "plugin_version": {"type": "string"},
                    "client_os": {"type": "string"},
                    "skill_name": {"type": "string"},
                    "started_at": {"type": "string"},
                    # Retest
                    "parent_audit_id": {"type": "string"},
                    "retest_number": {"type": "integer"},
                    "findings_to_retest": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["asset_name", "asset_type", "target_url"],
            },
        ),
        Tool(
            name="submit_finding",
            description="Registrar un hallazgo de seguridad (modelo rico).",
            inputSchema={
                "type": "object",
                "properties": {
                    "audit_id": {"type": "string"},
                    "title": {"type": "string"},
                    "severity": {"type": "string", "enum": sorted(VALID_SEVERITIES)},
                    "check_id": {"type": "string"},
                    "category": {"type": "string"},
                    "owasp_id": {"type": "string"},
                    "affected_resource": {"type": "string"},
                    "cvss_score": {"type": "number"},
                    "cvss_vector": {"type": "string"},
                    "endpoint": {"type": "string"},
                    "source_file": {"type": "string"},
                    "description": {"type": "string"},
                    "evidence": {"type": "object"},
                    "dynamic_validation": {"type": "object"},
                    "triage": {"type": "object"},
                    "cwe_id": {"type": "string"},
                    "owasp_category": {"type": "string"},
                    "detection_tool": {"type": "string"},
                    "confidence": {"type": "string", "enum": sorted(VALID_CONFIDENCE)},
                    # Retest
                    "parent_finding_id": {"type": "string"},
                    "retest_status": {"type": "string", "enum": sorted(VALID_RETEST_STATUS)},
                    "retest_notes": {"type": "string"},
                },
                "required": ["audit_id", "title", "severity"],
            },
        ),
        Tool(
            name="submit_event",
            description=(
                "Registrar un evento de la auditoría. event_types (MAYUSCULA): "
                "AUDIT_STARTED, AUDIT_COMPLETED, AUDIT_FAILED, AUDIT_PAUSED, AUDIT_RESUMED, "
                "CHECKPOINT_UPDATED, FINDING_DISCOVERED, TRIAGE_COMPLETED, REPORT_GENERATED, "
                "SKILL_INVOKED, FLOW_BRANCH."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "audit_id": {"type": "string"},
                    "event_type": {"type": "string"},
                    "message": {"type": "string"},
                    "findings_count": {"type": "integer"},
                    "severities": {"type": "object"},
                    "duration_seconds": {"type": "integer"},
                    "report_path": {"type": "string"},
                    "report_sha256": {"type": "string"},
                    "checkpoint": {"type": "object"},
                    "context": {"type": "object"},
                },
                "required": ["event_type"],
            },
        ),
        Tool(
            name="submit_llm_session",
            description=(
                "Registrar o actualizar una sesión de ataque a chatbot/LLM "
                "(colección llm_attack_sessions). Idempotente por session_id (upsert)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "audit_id": {"type": "string"},
                    "channel": {"type": "string"},
                    "mode": {"type": "string"},
                    "language": {"type": "string"},
                    "status": {"type": "string"},
                    "session": {"type": "object"},
                },
                "required": ["session_id", "audit_id"],
            },
        ),
        Tool(
            name="update_finding_triage",
            description=(
                "Actualizar el triage (priorización) de un finding propio: "
                "exploitability_score, recommended_action, risk_score y, opcionalmente, "
                "cvss_score/cvss_vector recalculados. No cambia el estado del finding."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "finding_id": {"type": "string"},
                    "exploitability_score": {"type": "number"},
                    "recommended_action": {
                        "type": "string",
                        "enum": ["EXPLOIT_IMMEDIATELY", "EXPLOIT_IF_TIME", "MONITOR"],
                    },
                    "risk_score": {"type": "number"},
                    "notes": {"type": "string"},
                    "cvss_score": {"type": "number"},
                    "cvss_vector": {"type": "string"},
                },
                "required": ["finding_id", "recommended_action"],
            },
        ),
        Tool(
            name="get_audits",
            description="Listar auditorías registradas (solo las del usuario autenticado)",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10},
                    "status": {"type": "string"},
                    "audit_type": {"type": "string"},
                },
            },
        ),
        Tool(
            name="get_audit_findings",
            description="Obtener los hallazgos de una auditoría (solo si es propia)",
            inputSchema={
                "type": "object",
                "properties": {"audit_id": {"type": "string"}},
                "required": ["audit_id"],
            },
        ),
        Tool(
            name="update_finding_review",
            description=(
                "Actualizar el estado de un finding propio. `status` es el estado del "
                "ciclo de vida (OPEN/FIXED/FALSE_POSITIVE/WONT_FIX/ACCEPTED_RISK/...). "
                "review_note (>=10 chars) es obligatoria al cerrar (FIXED/FALSE_POSITIVE/"
                "WONT_FIX/ACCEPTED_RISK). En retest usar retest_status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "finding_id": {"type": "string"},
                    "status": {"type": "string", "enum": sorted(VALID_FINDING_STATUS)},
                    "decision": {"type": "string", "enum": sorted(VALID_ANALYST_DECISIONS)},
                    "review_note": {"type": "string"},
                    "retest_status": {"type": "string", "enum": sorted(VALID_RETEST_STATUS)},
                    "original_severity": {"type": "string", "enum": sorted(VALID_SEVERITIES)},
                    "new_severity": {"type": "string", "enum": sorted(VALID_SEVERITIES)},
                },
                "required": ["finding_id", "status"],
            },
        ),
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict):
    identity = current_identity()
    if not identity:
        return _unauthorized("Identidad no establecida (falta autenticación)")

    # --- submit_audit ---
    if name == "submit_audit":
        target_url = arguments.get("target_url", "")
        ok, scope_error = _validate_target_url(target_url)
        if not ok:
            _log_event(
                "SCOPE_REJECTED",
                message=scope_error,
                level_log="WARNING",
                context={
                    "target_url": target_url,
                    "reason": scope_error,
                    "skill_name": arguments.get("skill_name", ""),
                },
            )
            return _err("target_out_of_scope", scope_error)

        audit_type = arguments.get("audit_type", "APROBACION_ACTIVOS")
        if audit_type not in VALID_AUDIT_TYPES:
            return _err("invalid_audit_type",
                        f"audit_type inválido. Valores: {sorted(VALID_AUDIT_TYPES)}")

        modality = arguments.get("modality", "WHITE_BOX")
        if modality not in VALID_MODALITIES:
            return _err("invalid_modality",
                        f"modality inválida. Valores: {sorted(VALID_MODALITIES)}")

        # Retest: validar ownership de la auditoría padre.
        parent_audit_id = arguments.get("parent_audit_id")
        if audit_type == "RETEST_APROBACION":
            if not parent_audit_id:
                return _err("parent_required",
                            "RETEST_APROBACION requiere parent_audit_id.")
            parent = db.audit_runs.find_one({"audit_id": parent_audit_id, "owner": identity})
            if not parent:
                return _unauthorized("Auditoría padre no encontrada o no autorizada.")

        today_count = db.audit_runs.count_documents({
            "owner": identity,
            "created_at": {"$gte": _today_start_iso()},
        }) if DAILY_AUDIT_LIMIT else 0
        if DAILY_AUDIT_LIMIT and today_count >= DAILY_AUDIT_LIMIT:
            retry_after = _seconds_until_midnight()
            _log_event(
                "RATE_LIMIT_HIT",
                message=f"Daily audit limit reached ({DAILY_AUDIT_LIMIT})",
                level_log="WARNING",
                context={
                    "limit": DAILY_AUDIT_LIMIT,
                    "used_today": today_count,
                    "retry_after": retry_after,
                    "skill_name": arguments.get("skill_name", ""),
                },
            )
            return _err(
                "daily_limit_exceeded",
                (f"Límite diario alcanzado ({DAILY_AUDIT_LIMIT} auditorías/día). "
                 "Reintenta después de medianoche (00:00)."),
                retry_after=retry_after, limit=DAILY_AUDIT_LIMIT, used_today=today_count,
            )

        slug = arguments["asset_name"].lower().replace(" ", "-")[:30]
        base_id = f"plugin_{_now().strftime('%Y-%m-%d')}_{slug}"
        started_at = arguments.get("started_at") or _iso_now()

        doc = {
            "source": "developer_plugin",
            "executed_by": identity,
            "owner": identity,
            "client_ip": current_client_ip(),
            "performed_by": current_performed_by() or None,
            "department": current_department(),
            "project_name": arguments.get("project_name") or arguments["asset_name"],
            "asset_name": arguments["asset_name"],
            "asset_type": arguments["asset_type"],
            "target_url": target_url,
            "audit_type": audit_type,
            "modality": modality,
            "docker_container": arguments.get("docker_container", ""),
            "docker_image": arguments.get("docker_image", ""),
            "source_code_path": arguments.get("source_code_path", ""),
            "language": arguments.get("language", ""),
            "framework": arguments.get("framework", ""),
            "repository_url": arguments.get("repository_url", ""),
            "has_auth": arguments.get("has_auth", False),
            "tier_1_approved": True,
            "tier_2_approved": False,
            "parent_audit_id": parent_audit_id,
            "retest_number": int(arguments.get("retest_number", 0)),
            "findings_to_retest": arguments.get("findings_to_retest", []),
            "status": "IN_PROGRESS",
            "plugin_version": arguments.get("plugin_version", ""),
            "client_os": arguments.get("client_os", ""),
            "skill_name": arguments.get("skill_name", ""),
            "started_at": started_at,
            "created_at": _iso_now(),
            "updated_at": _iso_now(),
            "completed_at": None,
            "duration_seconds": None,
            "findings_count": 0,
            "severities": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
            "dictamen": None,
            "dictamen_conditions": None,
            "report_path": None,
            "report_sha256": None,
            "checkpoint": None,
            "retest_comparison": None,
        }

        audit_id = base_id
        counter = 2
        while True:
            try:
                db.audit_runs.insert_one({**doc, "audit_id": audit_id})
                break
            except pymongo.errors.DuplicateKeyError:
                audit_id = f"{base_id}-{counter}"
                counter += 1
                if counter > 99:
                    raise
            except (pymongo.errors.WriteError, pymongo.errors.OperationFailure) as e:
                if _is_validation_error(e):
                    return _validation_err(e)
                raise

        _log_event(
            "AUDIT_STARTED",
            audit_id=audit_id,
            message=f"Audit started for {arguments['asset_name']}",
            context={
                "skill_name": arguments.get("skill_name", ""),
                "plugin_version": arguments.get("plugin_version", ""),
                "client_os": arguments.get("client_os", ""),
                "asset_type": arguments["asset_type"],
                "audit_type": audit_type,
                "target_url": target_url,
                "repository_url": arguments.get("repository_url", ""),
            },
        )

        return [TextContent(type="text", text=json.dumps({
            "success": True,
            "audit_id": audit_id,
            "message": f"Auditoría registrada: {audit_id}"
        }))]

    # --- submit_finding ---
    if name == "submit_finding":
        audit_id = arguments["audit_id"]

        audit = db.audit_runs.find_one({"audit_id": audit_id, "owner": identity})
        if not audit:
            return _unauthorized("Auditoría no encontrada o no autorizada.")

        severity = arguments["severity"]
        if severity not in VALID_SEVERITIES:
            return _err("invalid_severity",
                        f"severity inválida. Valores: {sorted(VALID_SEVERITIES)}")

        retest_status = arguments.get("retest_status")
        if retest_status is not None and retest_status not in VALID_RETEST_STATUS:
            return _err("invalid_retest_status",
                        f"retest_status inválido. Valores: {sorted(VALID_RETEST_STATUS)}")

        count = db.findings.count_documents({"audit_id": audit_id})
        finding_num = count + 1
        finding_id = f"{audit_id}_F{finding_num:03d}"

        doc = {
            "finding_id": finding_id,
            "display_id": f"F-{finding_num:03d}",
            "audit_id": audit_id,
            "owner": identity,
            "department": current_department(),
            "source": "developer_plugin",
            "check_id": arguments.get("check_id", ""),
            "title": arguments["title"],
            "description": arguments.get("description", ""),
            "severity": severity,
            "category": arguments.get("category"),
            "owasp_id": arguments.get("owasp_id"),
            "affected_resource": arguments.get("affected_resource"),
            "endpoint": arguments.get("endpoint", ""),
            "source_file": arguments.get("source_file", ""),
            "evidence": arguments.get("evidence", {}),
            "cvss_score": arguments.get("cvss_score"),
            "cvss_vector": arguments.get("cvss_vector"),
            "triage": arguments.get("triage"),
            "dynamic_validation": arguments.get("dynamic_validation"),
            "cwe_id": arguments.get("cwe_id", ""),
            "owasp_category": arguments.get("owasp_category", ""),
            "detection_tool": arguments.get("detection_tool", ""),
            "confidence": arguments.get("confidence", "suspected"),
            "status": "OPEN",
            "analyst_review": {
                "decision": "PENDING", "comment": None,
                "reviewed_by": None, "reviewed_at": None,
            },
            "parent_finding_id": arguments.get("parent_finding_id"),
            "retest_status": retest_status,
            "retest_notes": arguments.get("retest_notes"),
            "created_at": _iso_now(),
            "updated_at": None,
        }

        try:
            db.findings.insert_one(doc)
        except (pymongo.errors.WriteError, pymongo.errors.OperationFailure) as e:
            if _is_validation_error(e):
                return _validation_err(e)
            raise

        _log_event(
            "FINDING_DISCOVERED",
            audit_id=audit_id,
            message=f"Finding {finding_id}: {arguments['title']}",
            context={
                "finding_id": finding_id,
                "severity": severity,
                "check_id": arguments.get("check_id", ""),
                "detection_tool": arguments.get("detection_tool", ""),
            },
        )

        return [TextContent(type="text", text=json.dumps({
            "success": True,
            "finding_id": finding_id,
            "message": f"Hallazgo registrado: {arguments['title']}"
        }))]

    # --- submit_event ---
    if name == "submit_event":
        event_type = arguments["event_type"]
        audit_id = arguments.get("audit_id")

        if audit_id:
            audit = db.audit_runs.find_one({"audit_id": audit_id, "owner": identity})
            if not audit:
                return _unauthorized("Auditoría no encontrada o no autorizada.")

        extra_context = arguments.get("context") or {}
        context = {
            "findings_count": arguments.get("findings_count"),
            "severities": arguments.get("severities"),
            "duration_seconds": arguments.get("duration_seconds"),
            "report_path": arguments.get("report_path"),
            "report_sha256": arguments.get("report_sha256"),
            **extra_context,
        }
        context = {k: v for k, v in context.items() if v is not None}

        _log_event(event_type, audit_id=audit_id,
                   message=arguments.get("message", ""), context=context)

        try:
            # CHECKPOINT_UPDATED: persistir el checkpoint en audit_runs para resume.
            if event_type == "CHECKPOINT_UPDATED" and audit_id and arguments.get("checkpoint"):
                cp = arguments["checkpoint"]
                cp.setdefault("last_activity", _iso_now())
                db.audit_runs.update_one(
                    {"audit_id": audit_id, "owner": identity},
                    {"$set": {"checkpoint": cp, "updated_at": _iso_now()}},
                )

            # REPORT_GENERATED: persistir ruta + hash del informe para el gate de CI.
            if event_type == "REPORT_GENERATED" and audit_id:
                rep_set = {"updated_at": _iso_now()}
                if arguments.get("report_path") is not None:
                    rep_set["report_path"] = arguments["report_path"]
                if arguments.get("report_sha256") is not None:
                    rep_set["report_sha256"] = arguments["report_sha256"]
                if len(rep_set) > 1:
                    db.audit_runs.update_one(
                        {"audit_id": audit_id, "owner": identity}, {"$set": rep_set})

            # AUDIT_COMPLETED: propagar stats + calcular dictamen / retest_comparison.
            if event_type == "AUDIT_COMPLETED" and audit_id:
                audit = db.audit_runs.find_one({"audit_id": audit_id, "owner": identity})
                update_set = {
                    "status": "COMPLETED",
                    "findings_count": arguments.get("findings_count", 0),
                    "severities": arguments.get("severities", {}),
                    "updated_at": _iso_now(),
                    "completed_at": _iso_now(),
                }
                if arguments.get("duration_seconds") is not None:
                    update_set["duration_seconds"] = arguments["duration_seconds"]
                if arguments.get("report_path") is not None:
                    update_set["report_path"] = arguments["report_path"]
                if arguments.get("report_sha256") is not None:
                    update_set["report_sha256"] = arguments["report_sha256"]

                dictamen, conditions = _compute_dictamen(audit_id)
                update_set["dictamen"] = dictamen
                update_set["dictamen_conditions"] = conditions
                update_set["dictamen_confirmed_by"] = identity
                update_set["dictamen_confirmed_at"] = _iso_now()

                if audit and audit.get("audit_type") == "RETEST_APROBACION":
                    update_set["retest_comparison"] = _compute_retest_comparison(
                        audit_id, audit.get("parent_audit_id"))

                db.audit_runs.update_one(
                    {"audit_id": audit_id, "owner": identity}, {"$set": update_set})
        except (pymongo.errors.WriteError, pymongo.errors.OperationFailure) as e:
            if _is_validation_error(e):
                return _validation_err(e)
            raise

        return [TextContent(type="text", text=json.dumps({
            "success": True, "message": f"Evento registrado: {event_type}"
        }))]

    # --- submit_llm_session ---
    if name == "submit_llm_session":
        audit_id = arguments["audit_id"]
        audit = db.audit_runs.find_one({"audit_id": audit_id, "owner": identity})
        if not audit:
            return _unauthorized("Auditoría no encontrada o no autorizada.")

        session_id = arguments["session_id"]
        session_doc = dict(arguments.get("session") or {})
        session_doc.update({
            "session_id": session_id,
            "audit_id": audit_id,
            "owner": identity,
            "updated_at": _iso_now(),
        })
        for key in ("channel", "mode", "language", "status"):
            if arguments.get(key) is not None:
                session_doc[key] = arguments[key]
        session_doc.setdefault("created_at", _iso_now())

        try:
            db.llm_attack_sessions.update_one(
                {"session_id": session_id, "owner": identity},
                {"$set": session_doc},
                upsert=True,
            )
        except (pymongo.errors.WriteError, pymongo.errors.OperationFailure) as e:
            if _is_validation_error(e):
                return _validation_err(e)
            raise

        return [TextContent(type="text", text=json.dumps({
            "success": True, "session_id": session_id,
            "message": f"Sesión LLM registrada: {session_id}"
        }))]

    # --- update_finding_triage ---
    if name == "update_finding_triage":
        finding_id = arguments["finding_id"]
        action = arguments["recommended_action"]
        if action not in ("EXPLOIT_IMMEDIATELY", "EXPLOIT_IF_TIME", "MONITOR"):
            return _err("invalid_action",
                        "recommended_action inválido (EXPLOIT_IMMEDIATELY|EXPLOIT_IF_TIME|MONITOR)")

        finding = db.findings.find_one({"finding_id": finding_id, "owner": identity})
        if not finding:
            return _unauthorized("Finding no encontrado o no autorizado.")

        triage = {
            "exploitability_score": arguments.get("exploitability_score"),
            "recommended_action": action,
            "risk_score": arguments.get("risk_score"),
            "scored_at": _iso_now(),
            "notes": arguments.get("notes"),
        }
        update_set = {"triage": triage, "updated_at": _iso_now()}
        if arguments.get("cvss_score") is not None:
            update_set["cvss_score"] = arguments["cvss_score"]
        if arguments.get("cvss_vector") is not None:
            update_set["cvss_vector"] = arguments["cvss_vector"]

        try:
            db.findings.update_one(
                {"finding_id": finding_id, "owner": identity}, {"$set": update_set})
        except (pymongo.errors.WriteError, pymongo.errors.OperationFailure) as e:
            if _is_validation_error(e):
                return _validation_err(e)
            raise

        return [TextContent(type="text", text=json.dumps({
            "success": True, "finding_id": finding_id, "recommended_action": action,
        }))]

    # --- get_audits ---
    if name == "get_audits":
        limit = arguments.get("limit", 10)
        query = {"owner": identity}
        if arguments.get("status"):
            query["status"] = arguments["status"]
        if arguments.get("audit_type"):
            query["audit_type"] = arguments["audit_type"]
        audits = list(
            db.audit_runs.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
        )
        return [TextContent(type="text", text=json.dumps({
            "success": True, "audits": audits, "count": len(audits),
        }, default=str))]

    # --- get_audit_findings ---
    if name == "get_audit_findings":
        audit_id = arguments["audit_id"]
        audit = db.audit_runs.find_one({"audit_id": audit_id, "owner": identity})
        if not audit:
            return _unauthorized("Auditoría no encontrada o no autorizada.")
        findings = list(
            db.findings.find({"audit_id": audit_id}, {"_id": 0}).sort("cvss_score", -1)
        )
        return [TextContent(type="text", text=json.dumps({
            "success": True, "findings": findings, "count": len(findings),
        }, default=str))]

    # --- update_finding_review ---
    if name == "update_finding_review":
        finding_id = arguments["finding_id"]
        new_status = arguments["status"]
        if new_status not in VALID_FINDING_STATUS:
            return _err("invalid_status",
                        f"status inválido. Valores: {sorted(VALID_FINDING_STATUS)}")

        review_note = (arguments.get("review_note") or "").strip()
        if new_status in CLOSING_STATUSES_REQUIRING_NOTE and len(review_note) < 10:
            return _err(
                "review_note_required",
                (f"Para marcar un finding como '{new_status}' debes incluir una "
                 "observación (review_note) de al menos 10 caracteres que describa la "
                 "decisión (ej. commit/PR, función afectada, sanitización aplicada, "
                 "o justificación del riesgo aceptado)."),
            )

        retest_status = arguments.get("retest_status")
        if retest_status is not None and retest_status not in VALID_RETEST_STATUS:
            return _err("invalid_retest_status",
                        f"retest_status inválido. Valores: {sorted(VALID_RETEST_STATUS)}")

        finding = db.findings.find_one({"finding_id": finding_id, "owner": identity})
        if not finding:
            return _unauthorized("Finding no encontrado o no autorizado.")

        # Inferir la decisión del analista si no se pasa explícita.
        decision = arguments.get("decision")
        if not decision:
            if new_status == "FALSE_POSITIVE":
                decision = "FALSE_POSITIVE"
            else:
                decision = "CONFIRMED"
        if decision not in VALID_ANALYST_DECISIONS:
            return _err("invalid_decision",
                        f"decision inválida. Valores: {sorted(VALID_ANALYST_DECISIONS)}")

        old_status = finding.get("status", "OPEN")
        analyst_review = {
            "decision": decision,
            "comment": review_note or None,
            "reviewed_by": identity,
            "reviewed_at": _iso_now(),
        }
        if decision == "DOWNGRADE":
            analyst_review["original_severity"] = arguments.get("original_severity")
            analyst_review["new_severity"] = arguments.get("new_severity")

        update_set = {
            "status": new_status,
            "analyst_review": analyst_review,
            "updated_at": _iso_now(),
        }
        if retest_status is not None:
            update_set["retest_status"] = retest_status
            update_set["retest_notes"] = review_note or None

        try:
            db.findings.update_one(
                {"finding_id": finding_id, "owner": identity}, {"$set": update_set})
        except (pymongo.errors.WriteError, pymongo.errors.OperationFailure) as e:
            if _is_validation_error(e):
                return _validation_err(e)
            raise

        _log_event(
            "FINDING_REVIEWED",
            audit_id=finding.get("audit_id"),
            message=f"Finding {finding_id}: {old_status} → {new_status}",
            context={
                "finding_id": finding_id,
                "old_status": old_status,
                "new_status": new_status,
                "decision": decision,
                "review_note": review_note,
            },
        )

        return [TextContent(type="text", text=json.dumps({
            "success": True,
            "finding_id": finding_id,
            "old_status": old_status,
            "new_status": new_status,
        }))]

    return _unauthorized(f"Tool desconocido: {name}")


# --- Starlette App ---


def _resolve_identity(request) -> str | None:
    if AUTH_MODE == "local":
        # Sin autenticación: un único owner local fijo.
        return AUDIT_OWNER

    if AUTH_MODE == "kong":
        identity = request.headers.get(IDENTITY_HEADER, "").strip()
        return identity or None

    if AUTH_MODE == "bearer":
        expected = CONFIG["auth"]["api_key"]
        if not expected:
            logger.warning("GATEWAY_API_KEY not configured — all requests will be rejected")
            return None
        auth = request.headers.get("authorization", "")
        token = auth[7:] if auth.startswith("Bearer ") else ""
        if token != expected:
            return None
        return AUDIT_OWNER

    logger.error(f"AUTH_MODE desconocido: {AUTH_MODE}")
    return None


def create_app():
    session_manager = StreamableHTTPSessionManager(
        app=mcp,
        json_response=False,
        stateless=False,
    )

    async def handle_mcp(scope, receive, send):
        request = Request(scope, receive=receive)
        client_ip = _extract_client_ip(request)
        identity = _resolve_identity(request)

        if not identity:
            if AUTH_MODE == "kong":
                msg = f"Falta header {IDENTITY_HEADER} (debe ser inyectado por Kong)"
            else:
                msg = "API key inválida. Envía header Authorization: Bearer <api_key>"
            _log_event(
                "AUTH_FAILED",
                message=msg,
                level_log="WARNING",
                owner="",
                client_ip=client_ip,
                context={"auth_mode": AUTH_MODE, "reason": msg, "path": "/mcp"},
            )
            response = JSONResponse({"error": msg}, status_code=401)
            await response(scope, receive, send)
            return

        id_tok = _identity_ctx.set(identity)
        ip_tok = _client_ip_ctx.set(client_ip)
        pb_tok = _performed_by_ctx.set(_build_performed_by(request))
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            _identity_ctx.reset(id_tok)
            _client_ip_ctx.reset(ip_tok)
            _performed_by_ctx.reset(pb_tok)

    async def handle_tool_calls(request):
        """POST /tool-calls — recibe invocaciones Kali/browser desde PostToolUse hook."""
        client_ip = _extract_client_ip(request)
        identity = _resolve_identity(request)
        if not identity:
            _log_event(
                "AUTH_FAILED",
                message="auth failed on /tool-calls",
                level_log="WARNING",
                owner="",
                client_ip=client_ip,
                context={"auth_mode": AUTH_MODE, "path": "/tool-calls"},
            )
            return JSONResponse({"error": "unauthorized"}, status_code=401)

        pb = _build_performed_by(request)

        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"body inválido: {e}"}, status_code=400)

        calls = body.get("calls") if isinstance(body, dict) else None
        if not isinstance(calls, list) or not calls:
            return JSONResponse(
                {"error": "Se requiere {calls: [...]} con al menos 1 elemento"},
                status_code=400,
            )

        docs = []
        rejected = []
        for i, c in enumerate(calls):
            if not isinstance(c, dict):
                rejected.append({"index": i, "reason": "no es objeto"})
                continue
            tool_server = str(c.get("tool_server", "")).upper()
            tool_name = str(c.get("tool_name", "")).strip()
            if tool_server not in VALID_TOOL_SERVERS:
                rejected.append({"index": i, "reason": f"tool_server inválido: {tool_server}"})
                continue
            if not tool_name:
                rejected.append({"index": i, "reason": "tool_name vacío"})
                continue
            try:
                duration_ms = int(c.get("duration_ms", 0))
            except (TypeError, ValueError):
                rejected.append({"index": i, "reason": "duration_ms no es int"})
                continue
            if duration_ms < 0:
                rejected.append({"index": i, "reason": "duration_ms negativo"})
                continue

            docs.append({
                "owner": identity,
                "department": pb.get("department", ""),
                "audit_id": c.get("audit_id"),
                "timestamp": c.get("timestamp") or _iso_now(),
                "tool_server": tool_server,
                "tool_name": tool_name,
                "arguments_summary": c.get("arguments_summary") or {},
                "duration_ms": duration_ms,
                "success": bool(c.get("success", True)),
                "error": c.get("error"),
                "plugin_version": c.get("plugin_version", ""),
                "client_os": c.get("client_os", ""),
                "client_ip": client_ip,
            })

        inserted = 0
        if docs:
            try:
                result = db.tool_calls.insert_many(docs, ordered=False)
                inserted = len(result.inserted_ids)
            except Exception as e:
                logger.warning(f"insert_many tool_calls falló: {e}")
                return JSONResponse(
                    {"error": f"fallo al insertar: {e}", "inserted": 0},
                    status_code=500,
                )

        return JSONResponse({"inserted": inserted, "rejected": rejected})

    async def health(request):
        try:
            mongo_client.admin.command("ping")
            mongo_ok = True
        except Exception:
            mongo_ok = False

        return JSONResponse({
            "status": "healthy" if mongo_ok else "degraded",
            "mongodb": "connected" if mongo_ok else "disconnected",
            "auth_mode": AUTH_MODE,
            "path_prefix": PREFIX,
            "daily_audit_limit": DAILY_AUDIT_LIMIT,
        })

    routes = [
        Route(f"{PREFIX}/health", health),
        Mount(f"{PREFIX}/mcp", app=handle_mcp),
        Route(f"{PREFIX}/tool-calls", handle_tool_calls, methods=["POST"]),
    ]
    if PREFIX:
        routes.insert(0, Route("/health", health))

    @asynccontextmanager
    async def lifespan(app):
        async with session_manager.run():
            yield

    return Starlette(routes=routes, lifespan=lifespan)


if __name__ == "__main__":
    app = create_app()
    port = CONFIG["server"]["port"]
    logger.info(
        f"Pentest Gateway starting on port {port} "
        f"(prefix={PREFIX or '/'} auth_mode={AUTH_MODE} owner={AUDIT_OWNER})"
    )
    uvicorn.run(app, host="0.0.0.0", port=port)
