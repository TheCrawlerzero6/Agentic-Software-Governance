# Schema: Event — Plugin para Desarrolladores

> **Fuente de verdad para la coleccion `events`.**
> Leer este archivo ANTES de insertar un documento en `events` (via `submit_event`).
> Mismo modelo de referencia: los `event_type`, `level_log` y `tool_server`
> van en **MAYUSCULA**.
>
> ⚠️ **Validacion en el gateway:** `events` se valida con `$jsonSchema` (`init-mongo-schema.js`):
> `level_log` debe ser INFO/WARNING/ERROR y `event_type`/`timestamp`/`level_log` son
> obligatorios. Un `event_type` fuera del set canonico se acepta pero se marca
> `deprecated_schema`. Como llamar a `submit_event`: `@reference/gateway-persistence.md`.

---

## Tipos base

```typescript
type EventType =
  // Ciclo de vida del comando
  | "SKILL_INVOKED"        // al entrar a /pentesting o /mis-auditorias
  | "FLOW_BRANCH"          // al bifurcar a un sub-flow
  // Ciclo de vida de la auditoria
  | "AUDIT_STARTED"
  | "AUDIT_COMPLETED"
  | "AUDIT_FAILED"
  | "AUDIT_PAUSED"
  | "AUDIT_RESUMED"
  | "CHECKPOINT_UPDATED"   // tras completar un check o grupo (resume)
  // Hallazgos
  | "FINDING_DISCOVERED"   // guardado incremental de cada finding
  | "FINDING_REVIEWED"     // al actualizar status/analyst_review
  // Cierre
  | "TRIAGE_COMPLETED"
  | "REPORT_GENERATED"
  // Rechazos del servidor (server-auto)
  | "SCOPE_REJECTED"
  | "RATE_LIMIT_HIT"
  | "AUTH_FAILED"
  // Telemetria de herramientas
  | "TOOL_CALL"
  | "ERROR";

type LevelLog   = "INFO" | "WARNING" | "ERROR";
type ToolServer = "KALI" | "BROWSER";
```

---

## Interfaz principal

```typescript
interface Event {
  _id?:          string;
  audit_id:      string | null;     // null/"" para eventos sin auditoria (SKILL_INVOKED)
  owner?:        string;            // resuelto por el gateway
  project_name?: string;
  event_type:    EventType;
  level_log:     LevelLog;
  timestamp:     string;            // ISO 8601 (UTC, -05:00)
  message?:      string;
  context?:      object;            // estructura variable segun event_type (ver abajo)
  deprecated_schema?: boolean;      // true = registro con esquema viejo/no canonico, excluir de dashboards
}
```

> **`deprecated_schema`** (igual que en el modelo de referencia): los registros con un
> `event_type` que NO esta en la lista canonica de arriba (telemetria vieja/experimental
> como `PHASE_START`, `GROUP_COMPLETED`, etc.) se marcan `deprecated_schema: true`. Todas
> las queries de analitica/dashboard deben filtrar con `deprecated_schema: { $ne: true }`.

---

## `context` por `event_type`

| event_type | context |
|---|---|
| `SKILL_INVOKED` | `{ skill_name, plugin_version, client_os, source }` |
| `FLOW_BRANCH` | `{ command, branch, source }` |
| `AUDIT_STARTED` | `{ asset_name, asset_type, target_url, repository_url, source_code_path }` |
| `AUDIT_COMPLETED` | `{ findings_count, severities, duration_seconds, dictamen, report_path, report_sha256 }` |
| `AUDIT_FAILED` | `{ reason }` |
| `CHECKPOINT_UPDATED` | `{ check_id, agent, group, completed_checks[], completed_groups[] }` |
| `FINDING_DISCOVERED` | `{ finding_id, severity, check_id, agent, group }` |
| `FINDING_REVIEWED` | `{ finding_id, old_status, new_status, decision, review_note }` |
| `TRIAGE_COMPLETED` | `{ exploit_immediately, exploit_if_time, monitor }` |
| `REPORT_GENERATED` | `{ report_path, size_bytes, report_sha256 }` |
| `SCOPE_REJECTED` | `{ target_url, reason, skill_name }` (server-auto) |
| `RATE_LIMIT_HIT` | `{ limit, used_today, retry_after, skill_name }` (server-auto) |
| `AUTH_FAILED` | `{ auth_mode, reason, path }` (server-auto) |
| `TOOL_CALL` | `{ tool_server, tool_name, arguments_summary, success, error, duration_ms, plugin_version, client_os }` |
| `ERROR` | `{ message, where }` |

> **Telemetria de herramientas:** cada invocacion de una tool de Kali o Browser se
> registra automaticamente via el hook `hooks/telemetry-tool-call.sh` (PostToolUse),
> que envia al endpoint dedicado `/tool-calls` del gateway. Los argumentos se sanitizan
> (sin password/token/secret/apikey). El `tool_server` se normaliza a `KALI`/`BROWSER`.

---

## Ejemplos

### SKILL_INVOKED
```json
{
  "audit_id": "",
  "event_type": "SKILL_INVOKED",
  "level_log": "INFO",
  "timestamp": "2026-05-31T14:55:00-05:00",
  "context": { "skill_name": "pentesting", "plugin_version": "1.2.0", "client_os": "win32", "source": "developer_plugin" }
}
```

### FINDING_DISCOVERED
```json
{
  "audit_id": "plugin_2026-05-31_mi-api",
  "project_name": "Mi API",
  "event_type": "FINDING_DISCOVERED",
  "level_log": "INFO",
  "timestamp": "2026-05-31T15:25:00-05:00",
  "context": { "finding_id": "plugin_mi-api_F001", "severity": "CRITICAL", "check_id": "api3_sqli", "agent": "pentester-api", "group": "G1" }
}
```

### CHECKPOINT_UPDATED
```json
{
  "audit_id": "plugin_2026-05-31_mi-api",
  "event_type": "CHECKPOINT_UPDATED",
  "level_log": "INFO",
  "timestamp": "2026-05-31T15:30:00-05:00",
  "context": { "group": "G1", "agent": "pentester-api", "completed_checks": ["api1_bola", "api3_sqli"], "completed_groups": ["G1"] }
}
```

### REPORT_GENERATED
```json
{
  "audit_id": "plugin_2026-05-31_mi-api",
  "event_type": "REPORT_GENERATED",
  "level_log": "INFO",
  "timestamp": "2026-05-31T17:00:00-05:00",
  "context": { "report_path": "audits/2026-05-31_mi-api/security-report.md", "size_bytes": 24500, "report_sha256": "sha256..." }
}
```
