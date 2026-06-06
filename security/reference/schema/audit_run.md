# Schema: AuditRun — Plugin para Desarrolladores

> **Fuente de verdad para la coleccion `audit_runs`.**
> Leer este archivo ANTES de insertar o actualizar un documento en `audit_runs`.
> El documento que insertes DEBE satisfacer la interfaz `AuditRun` exactamente.
>
> Este esquema es el mismo modelo rico de referencia, **acotado a lo que un
> desarrollador necesita**: solo dos tipos de auditoria (`APROBACION_ACTIVOS` y
> `RETEST_APROBACION`) y solo los tipos de activo web / api / chatbot / n8n.
> El activo auditado es **de la propia autoria del desarrollador**.
>
> ⚠️ **Validacion en el gateway:** este documento se valida con un `$jsonSchema` de MongoDB
> (`init-mongo-schema.js`); los inserts/updates malformados se **RECHAZAN**. No insertas
> directo: usas las tools del gateway (`submit_audit`, `submit_event`). Como construir los
> argumentos: `@reference/gateway-persistence.md`.

---

## Tipos base

```typescript
type ClientOS      = "WINDOWS" | "MAC" | "LINUX";
type Modality      = "WHITE_BOX" | "GRAY_BOX" | "BLACK_BOX" | "MIXED";
type AuditType     = "APROBACION_ACTIVOS" | "RETEST_APROBACION";   // SOLO estos dos
type AuditStatus   = "PENDING" | "IN_PROGRESS" | "PAUSED" | "COMPLETED" | "CANCELLED";
type NetworkAccess = "EXTERNAL" | "INTERNAL" | "INTERNAL_VPN" | "LOCAL";
type ConnectionMode = "LOCAL" | "REMOTE" | "HYBRID";
```

---

## Interfaces de targets

> Solo estos 5 tipos estan soportados en el plugin de desarrolladores.
> Las claves presentes en `targets` determinan que agentes especializados se lanzan.

```typescript
interface ApiTarget {
  nombre:       string;
  open_api_url: string | null;   // URL del Swagger/OpenAPI si existe
  base_url:     string | null;
  code:         boolean;         // true = codigo fuente disponible (Caja Blanca)
  modality:     Modality;
}

interface WebTarget {
  nombre: string;
  url:    string;
}

interface ChatbotTarget {
  nombre:           string;
  subtype:          "web_widget" | "http_api" | "whatsapp" | "telegram" | "messenger" | "slack" | "other";
  mode:             "automated" | "manual";
  language:         "es" | "en" | "multilingual";
  model_endpoint:   string | null;   // "openai:gpt-4o-mini", "anthropic:claude-3-haiku", etc.
  has_rag:          boolean;
  has_tools:        boolean;
  tools_count:      number;
  has_memory:       boolean;
  has_multi_tenant: boolean;
  url:              string | null;
}

interface N8nFlujoTarget {
  nombre:    string;
  modality:  Modality;
  url:       string | null;
  json:      string;          // nombre del archivo JSON exportado del workflow
  hash_json: string;          // SHA-256 del archivo JSON
}

interface NodeN8nTarget {
  nombre:   string;
  modality: Modality;
  hash_zip: string;           // SHA-256 del ZIP / del codigo del nodo custom
}

// Al menos una clave presente. El plugin de devs NO soporta active_directory,
// cloud, network ni osint (eso es exclusivo de referencia).
interface Targets {
  api?:       ApiTarget[];
  web?:       WebTarget[];
  chatbot?:   ChatbotTarget[];
  n8n_flujo?: N8nFlujoTarget[];
  node_n8n?:  NodeN8nTarget[];
}
```

---

## Interfaces de personas

```typescript
interface QA {
  name:  string;
  email: string;
}

interface Recipient {
  company_name:   string;     // "ACME" para Aprobacion de Activos
  department:     string | null;
  recipient_name: string;
}
```

---

## Interfaces de trazabilidad

```typescript
interface PerformedBy {
  user:           string;        // owner local (AUDIT_OWNER, por defecto "local")
  custom_id:      string;        // vacío en modo local
  consumer_id:    string;        // vacío en modo local
  credential_id:  string;        // vacío en modo local
  department:     string;        // vacío en modo local
  purpose:        string;        // vacío en modo local
  key_issued_at:  number | null; // null en modo local
  key_expires_at: number | null; // null en modo local
  client_ip:      string;        // IP del cliente (loopback en local)
  auth_via:       string;        // "local" (por defecto) | "bearer"
}
```

> En modo local **no hay autenticación**: `owner`/`executed_by` (= `user`) y `performed_by`
> los fija **el gateway** con un único owner configurable (`AUDIT_OWNER`, por defecto
> `"local"`). El resto de campos de identidad quedan vacíos. NO se llenan desde el cliente.

---

## Interfaces de resultados

```typescript
interface WAF {
  detected:    boolean;
  provider:    string;    // "UNKNOWN" si no se identifica
  whitelisted: boolean;   // true si el entorno de prueba tiene el WAF en whitelist (recomendado)
}

interface Severities {
  critical: number;
  high:     number;
  medium:   number;
  low:      number;
  info:     number;
}

interface TriageSummary {
  exploit_immediately: number;
  exploit_if_time:     number;
  monitor:             number;
}

interface RetestComparison {
  original_audit_id: string;
  fixed:             number;
  partial:           number;
  unfixed:           number;
  new:               number;
  risk_direction:    "MEJORANDO" | "ESTABLE" | "EMPEORANDO";
  fixed_ids?:        string[];
  unfixed_ids?:      string[];
}
```

---

## Interfaz principal

```typescript
interface AuditRun {
  // -- Identidad --
  _id?:           string;        // ObjectId (auto)
  audit_id:       string;        // Formato: "plugin_YYYY-MM-DD_slug[-N]"
  source:         "developer_plugin";
  plugin_version: string;
  client_os:      ClientOS;

  // -- Trazabilidad (resuelto por el gateway) --
  owner:        string;          // identidad corporativa del dev (authZ) = performed_by.user
  executed_by:  string;
  department?:  string;          // área del dev (claim `departamento` del JWT) — ej. "SeguridadLogica"
  client_ip?:   string;
  performed_by?: PerformedBy;
  connection_mode?: ConnectionMode;

  // -- Scope --
  project_name: string;
  targets:      Targets;         // al menos una clave presente
  audit_type:   AuditType;       // APROBACION_ACTIVOS | RETEST_APROBACION
  modality:     Modality;        // normalmente WHITE_BOX (activo propio)
  scope_type?:   "full" | "module";  // full = toda la app; module = solo una parte
  scope_detail?: string | null;      // descripción del módulo + carpetas/prefijos (si module)

  // -- Repositorio (clave para el futuro gate de CI) --
  repository_url: string | null;

  // -- Personas --
  qa:        QA;
  reviewer:  string | null;
  recipient: Recipient;

  // -- Condiciones --
  network_access: NetworkAccess;
  credentials:    boolean;       // true si se entregaron credenciales de cada rol
  restrictions?:  string[];

  // -- WAF --
  waf: WAF;

  // -- Aprobaciones (Tier) --
  tier_1_approved: boolean;      // siempre true — checks de deteccion auto-aprobados
  tier_2_approved: boolean;      // herramientas de alto impacto (sqlmap intrusivo, etc.)

  // -- Vinculacion retest --
  parent_audit_id:     string | null;
  retest_number:       number;          // 0 = auditoria inicial
  findings_to_retest?: string[];

  // -- Estado y fechas --
  status:       AuditStatus;
  created_at:   string;          // ISO 8601 (UTC)
  updated_at:   string;
  started_at:   string | null;
  completed_at: string | null;
  duration_seconds?: number | null;

  // -- Resultados --
  findings_count:   number;      // inicializar en 0
  severities:       Severities;  // inicializar todo en 0
  triage_summary?:  TriageSummary;
  retest_comparison?: RetestComparison | null;   // solo en RETEST_APROBACION

  // -- Dictamen (Aprobacion de Activos / Retest) --
  dictamen?:              string | null;   // "SE APRUEBA" | "SE APRUEBA CON CONDICIONES" | "NO SE APRUEBA"
  dictamen_conditions?:   string | null;
  dictamen_confirmed_by?: string | null;
  dictamen_confirmed_at?: string | null;

  // -- Reporte + verificacion CI --
  report_path:    string | null;   // ruta local del security-report.md
  report_sha256?: string | null;   // hash del MD generado (para contrastar vs el repo en CI)

  // -- Checkpoint (resume) --
  checkpoint?: {
    completed_checks: string[];    // ["api1_bola", "web_a03_sqli"]
    completed_groups: string[];    // ["G1", "G2"]
    last_activity:    string;      // ISO 8601
  } | null;

  // -- Contexto adicional --
  objective?:        string | null;
}
```

---

## Documento inicial (al confirmar el plan)

```json
{
  "audit_id":       "plugin_YYYY-MM-DD_slug",
  "source":         "developer_plugin",
  "plugin_version": "",
  "client_os":      "WINDOWS",

  "project_name":   "",
  "targets":        {},
  "audit_type":     "APROBACION_ACTIVOS",
  "modality":       "WHITE_BOX",
  "scope_type":     "full",
  "scope_detail":   null,
  "repository_url": null,

  "qa":        { "name": "", "email": "" },
  "reviewer":  null,
  "recipient": { "company_name": "ACME", "department": null, "recipient_name": "" },

  "network_access": "LOCAL",
  "credentials":    false,
  "restrictions":   [],

  "waf": { "detected": false, "provider": "UNKNOWN", "whitelisted": false },

  "tier_1_approved": true,
  "tier_2_approved": false,

  "parent_audit_id":    null,
  "retest_number":      0,
  "findings_to_retest": [],

  "status":       "IN_PROGRESS",
  "created_at":   "2026-01-01T00:00:00-05:00",
  "updated_at":   "2026-01-01T00:00:00-05:00",
  "started_at":   "2026-01-01T00:00:00-05:00",
  "completed_at": null,

  "findings_count": 0,
  "severities":     { "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0 },

  "dictamen":     null,
  "report_path":  null,
  "checkpoint":   null,
  "objective":    null
}
```

---

## Update al completar

```json
{
  "$set": {
    "status":           "COMPLETED",
    "completed_at":     "2026-01-01T00:00:00-05:00",
    "updated_at":       "2026-01-01T00:00:00-05:00",
    "findings_count":   12,
    "severities":       { "critical": 0, "high": 2, "medium": 6, "low": 3, "info": 1 },
    "triage_summary":   { "exploit_immediately": 0, "exploit_if_time": 2, "monitor": 6 },
    "dictamen":         "SE APRUEBA CON CONDICIONES",
    "dictamen_conditions": "Corregir F-002 antes del paso a produccion.",
    "duration_seconds": 3600,
    "report_path":      "audits/{dir}/security-report.md",
    "report_sha256":    "sha256..."
  }
}
```

---

## Calculo automatico del dictamen

> **Premisa:** el dev debe dejar TODOS los findings en estado terminal (mitigado o
> justificado). El dictamen se calcula al `AUDIT_COMPLETED`, por buckets, sobre **todas**
> las severidades. Lo computa el gateway (`_compute_dictamen`).

Cada finding cae en un bucket:

| Bucket | Estados | Efecto |
|---|---|---|
| **pendiente** | cualquier estado no terminal: `OPEN` (sin clasificar o confirmada sin corregir), `PARTIAL_FIX`, `REOPENED`, … (cualquier severidad) | → **NO SE APRUEBA** |
| **bloqueado** | `FALSE_POSITIVE` en un finding **CRITICAL/HIGH** (impacto demostrado: no puede ser "comportamiento normal") | → **NO SE APRUEBA** + revisar con el equipo de seguridad |
| **condición** | `ACCEPTED_RISK` (riesgo aceptado) · `WONT_FIX`+`OUT_OF_SCOPE` (fuera de alcance) | → **CON CONDICIONES** |
| **limpio** | `FIXED` · `FALSE_POSITIVE` de baja/media/info | sin penalización |

| Resultado | Dictamen |
|---|---|
| ≥1 pendiente | `NO SE APRUEBA` (lista los `display_id` y pide mitigar/justificar) |
| Sin pendientes, ≥1 bloqueado | `NO SE APRUEBA` (razón + `tu equipo de seguridad`) |
| Sin pendientes ni bloqueados, ≥1 condición | `SE APRUEBA CON CONDICIONES` |
| Todo limpio | `SE APRUEBA` |

> El plugin (`review-loop.md`) ya impide marcar Falso positivo / Fuera de alcance un
> crítico/alto de código o dependencia propia (escenario 4); este cálculo es el backstop
> del servidor.

**Retest (`RETEST_APROBACION`):** el dictamen usa el **mismo** cálculo por buckets sobre los
findings hijos. Un hijo con `retest_status = FIXED` cuenta como **mitigado** (lo cierra el
plugin a `status=FIXED`, y el gateway lo trata como resuelto aunque quedara `OPEN`). Los
`PARTIAL`/`UNFIXED`/`REGRESSED` pasan por el cierre guiado: si no quedan resueltos o
justificados → `NO SE APRUEBA`. La `retest_comparison.risk_direction`
(MEJORANDO/ESTABLE/EMPEORANDO) es **informativa** (se muestra en el reporte como tendencia);
**no** altera el dictamen — lo que manda es que todo quede mitigado o justificado.

---

## Retest — vinculacion padre/hijo

```json
{
  "audit_id":          "plugin_2026-05-31_mi-api-retest1",
  "audit_type":        "RETEST_APROBACION",
  "parent_audit_id":   "plugin_2026-03-18_mi-api",
  "retest_number":     1,
  "findings_to_retest": ["plugin_mi-api_F001", "plugin_mi-api_F002"]
}
```

Al completar el retest se calcula `retest_comparison`:

```json
{
  "$set": {
    "retest_comparison": {
      "original_audit_id": "plugin_2026-03-18_mi-api",
      "fixed": 4, "partial": 1, "unfixed": 1, "new": 0,
      "risk_direction": "MEJORANDO"
    }
  }
}
```

`risk_direction`: `MEJORANDO` si `fixed > unfixed + new`; `ESTABLE` si iguales; `EMPEORANDO` si menor.

---

## Updates de estado (pausar / reanudar / cancelar)

```json
{ "$set": { "status": "PAUSED",     "updated_at": "..." } }
{ "$set": { "status": "IN_PROGRESS","updated_at": "..." } }
{ "$set": { "status": "CANCELLED",  "updated_at": "...", "completed_at": "..." } }
```

---

## Verificacion para el futuro gate de CI/CD

> El objetivo del informe Markdown NO es solo documentar: es **obligar al dev a pasar
> por el flujo de pentesting**. A futuro un step del pipeline de CI leera el
> `security-report.md` del directorio `pentesting/` del repo, extraera el `audit_id`
> + `repository_url` de su cabecera, y los contrastara contra esta coleccion via el
> endpoint `GET /audits/verify`.

Para que esto sea posible, este esquema ya guarda:
- `repository_url` — para enlazar la auditoria con el repo.
- `report_path` + `report_sha256` — para contrastar que el MD del repo es el que genero el plugin.
- `dictamen` + `status` — para que el gate decida si aprueba el merge/deploy.

El contrato del gate (a implementar despues): `valid = false` si el audit no esta
`COMPLETED`, si hay findings CRITICAL/HIGH `OPEN`, si el `repository_url` no coincide,
o si el `report_sha256` del repo no coincide con el de la BD.

---

## Ejemplos de targets

### API + Web
```json
{
  "targets": {
    "api": [{ "nombre": "Mi API", "open_api_url": "http://localhost:3000/swagger.json", "base_url": "http://localhost:3000", "code": true, "modality": "WHITE_BOX" }],
    "web": [{ "nombre": "Mi Portal", "url": "http://localhost:8080" }]
  }
}
```

### Chatbot
```json
{
  "targets": {
    "chatbot": [{
      "nombre": "Bot Soporte", "subtype": "web_widget", "mode": "automated", "language": "es",
      "model_endpoint": "openai:gpt-4o-mini", "has_rag": true, "has_tools": true,
      "tools_count": 3, "has_memory": true, "has_multi_tenant": false,
      "url": "http://localhost:3000/chat"
    }]
  }
}
```

### n8n workflow
```json
{
  "targets": {
    "n8n_flujo": [{ "nombre": "Flujo Onboarding", "modality": "WHITE_BOX", "url": null, "json": "onboarding.json", "hash_json": "sha256..." }]
  }
}
```

### Nodo custom n8n
```json
{
  "targets": {
    "node_n8n": [{ "nombre": "n8n-nodes-mi-integracion", "modality": "WHITE_BOX", "hash_zip": "sha256..." }]
  }
}
```
