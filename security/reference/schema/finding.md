# Schema: Finding — Plugin para Desarrolladores

> **Fuente de verdad para la coleccion `findings`.**
> Leer este archivo ANTES de insertar o actualizar un documento en `findings`.
> El documento que insertes DEBE satisfacer la interfaz `Finding` exactamente.
>
> Mismo modelo rico de referencia. Los enums van en **MAYUSCULA**.
> El estado de cierre vive en `status` + `analyst_review.decision` (no en un
> `review_status` plano). La traduccion a nombres amigables para el dev vive en
> `review-loop.md`.
>
> ⚠️ **Validacion en el gateway:** este documento se valida con un `$jsonSchema` de MongoDB
> (`init-mongo-schema.js`). Los inserts/updates con campos requeridos faltantes o enums
> invalidos se **RECHAZAN** (`error_code: schema_validation_failed`). Usa exactamente estos
> enums y campos. Como llamar a las tools del gateway: `@reference/gateway-persistence.md`.

---

## Tipos base

```typescript
type Severity      = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";
type FindingStatus = "OPEN" | "POTENTIAL" | "INFORMATIONAL" | "IN_REVIEW"
                   | "ACCEPTED_RISK" | "FIXED" | "PARTIAL_FIX" | "WONT_FIX"
                   | "FALSE_POSITIVE" | "REOPENED";
type RetestStatus  = "FIXED" | "PARTIAL" | "UNFIXED" | "REGRESSED" | null;
type TriageAction  = "EXPLOIT_IMMEDIATELY" | "EXPLOIT_IF_TIME" | "MONITOR";
type FindingSource = "developer_plugin";
type Confidence    = "confirmed" | "high" | "medium" | "low" | "suspected";
```

---

## Estados (TODOS los valores)

**`status` (FindingStatus):**
- `OPEN` — confirmado, no resuelto.
- `POTENTIAL` — posible, requiere validacion.
- `INFORMATIONAL` — bajo riesgo, solo informativo.
- `IN_REVIEW` — en revision.
- `ACCEPTED_RISK` — el dev/negocio acepta el riesgo (requiere nota).
- `FIXED` — remediado (requiere nota de como se corrigio).
- `PARTIAL_FIX` — parcialmente mitigado.
- `WONT_FIX` — no se remediara (requiere nota / justificacion).
- `FALSE_POSITIVE` — no es vulnerabilidad real (requiere nota).
- `REOPENED` — un retest mostro regresion.

**`analyst_review.decision`:**
- `PENDING` — aun no revisado (default).
- `CONFIRMED` — es una vulnerabilidad real.
- `OUT_OF_SCOPE` — fuera de alcance.
- `FALSE_POSITIVE` — no es real.
- `DOWNGRADE` — severidad reducida (incluir `original_severity` y `new_severity`).

**`retest_status`:** `FIXED` | `PARTIAL` | `UNFIXED` | `REGRESSED` | `null` (nunca re-testeado).

---

## Sub-objetos

```typescript
interface TechnicalAnalysis {
  weak_point:        string;
  root_cause:        string;
  observed_behavior: string;
  expected_behavior: string;
}

interface ConversationTurn {
  role:       "user" | "assistant";
  content:    string;
  timestamp:  string;   // ISO 8601 con timezone (-05:00)
  turn?:      number;
  prompt_id?: string;   // para trazabilidad del corpus, ej "PROMPT-LLM01-INJ-003-V1"
  latency_ms?: number;  // critico para LLM03-DOS / LLM10-CON
}

interface Evidence {
  screenshots:        string[];
  request:            string | null;
  response:           string | null;
  poc_steps:          string[];
  technical_analysis: TechnicalAnalysis;
  remediation:        string[];
  references:         string[];

  // Code review
  vulnerable_code?:   string | null;
  fix_suggestion?:    string | null;

  // Chatbot / LLM
  llm_check_id?:      string | null;        // "LLM01-INJ-003"
  conversation_log?:  ConversationTurn[];
  bypassed_defenses?: string[];
  affected_workflow?: string | null;        // tool/funcion del bot afectada
  model_endpoint?:    string | null;

  // n8n
  sec_id?:            string | null;        // "SEC-4b"
  node_name?:         string | null;        // nombre del nodo del workflow
}

interface Triage {
  exploitability_score: number;       // 0-10
  recommended_action:   TriageAction;
  risk_score:           number;        // 0-10
  scored_at:            string;        // ISO 8601
  notes:                string | null;
}

// Validacion por explotacion — HTTP 200 NO es confirmacion. Verificar efecto real.
interface DynamicValidation {
  validated:        boolean | null;    // true = EXPLOTABLE, false = NO EXPLOTABLE, null = no aplica
  validated_at:     string | null;
  payload_used:     string | null;     // payload no-destructivo (id, whoami, read-back)
  response_summary: string | null;
}

interface AnalystReview {
  decision:           "CONFIRMED" | "OUT_OF_SCOPE" | "FALSE_POSITIVE" | "DOWNGRADE" | "PENDING";
  comment:            string | null;
  reviewed_by:        string | null;   // auto desde la identidad del gateway
  reviewed_at:        string | null;
  original_severity?: Severity | null; // solo DOWNGRADE
  new_severity?:      Severity | null; // solo DOWNGRADE
}

interface RetestJustification {
  decision:     "PENDING_RETEST" | "ACCEPTED_RISK" | "FALSE_POSITIVE" | "OUT_OF_SCOPE";
  comment:      string;                // razon obligatoria
  justified_by: string;
  justified_at: string;
}
```

---

## Interfaz principal

```typescript
interface Finding {
  // -- Identidad --
  _id?:        string;
  finding_id:  string;       // "plugin_<slug>_F<NNN>"  ej: plugin_mi-api_F001
  display_id:  string;       // "F-NNN"                 ej: F-001
  audit_id:    string;
  owner:       string;       // identidad del dev (authZ, resuelto por el gateway)
  source:      FindingSource;
  check_id:    string;       // "api1_bola", "web_a03_sqli", "llm01_inj", "n8n_sec4b"

  // -- Descripcion --
  title:             string;
  description:       string | null;
  severity:          Severity;
  category:          string | null;   // "API1:2023 — BOLA"
  owasp_id:          string | null;   // "API1:2023", "A03:2021", "LLM01:2025"
  affected_resource: string | null;
  endpoint?:         string | null;   // metodo + path, ej "POST /api/login"

  // -- Evidencia --
  evidence: Evidence;

  // -- CVSS --
  cvss_score:  number | null;   // 0-10
  cvss_vector: string | null;

  // -- Analisis --
  triage:             Triage | null;
  dynamic_validation: DynamicValidation | null;

  // -- Estado --
  status: FindingStatus;       // inicializar en "OPEN"

  // -- Revision del analista (obligatoria antes de generar reporte) --
  analyst_review: AnalystReview;   // inicializar con decision "PENDING"

  // -- Retest --
  parent_finding_id:      string | null;
  retest_status:          RetestStatus;
  retest_notes:           string | null;
  retest_justification?:  RetestJustification | null;

  // -- Fechas --
  created_at: string;          // ISO 8601
  updated_at: string | null;

  // -- Extensions opcionales --
  cwe_id?:         string | null;   // "CWE-89"
  source_file?:    string | null;   // "src/controllers/auth.js:45"
  detection_tool?: string | null;   // "code-review", "sqlmap", "nuclei", "manual"
  confidence?:     Confidence;
}
```

---

## Documento inicial (al registrar el hallazgo)

```json
{
  "finding_id":  "plugin_<slug>_F001",
  "display_id":  "F-001",
  "audit_id":    "plugin_YYYY-MM-DD_slug",
  "source":      "developer_plugin",
  "check_id":    "",

  "title":             "",
  "description":       null,
  "severity":          "HIGH",
  "category":          null,
  "owasp_id":          null,
  "affected_resource": null,
  "endpoint":          null,

  "evidence": {
    "screenshots": [],
    "request":     null,
    "response":    null,
    "poc_steps":   [],
    "technical_analysis": {
      "weak_point": "", "root_cause": "", "observed_behavior": "", "expected_behavior": ""
    },
    "remediation": [],
    "references":  [],
    "vulnerable_code": null,
    "fix_suggestion":  null
  },

  "cvss_score":  null,
  "cvss_vector": null,

  "triage":             null,
  "dynamic_validation": null,

  "status": "OPEN",

  "analyst_review": { "decision": "PENDING", "comment": null, "reviewed_by": null, "reviewed_at": null },

  "parent_finding_id": null,
  "retest_status":     null,
  "retest_notes":      null,

  "created_at": "2026-01-01T00:00:00-05:00",
  "updated_at": null,

  "detection_tool": "code-review",
  "confidence":     "suspected"
}
```

---

## IDs

- `finding_id`: `{audit_id}_F{NNN}` — el gateway lo deriva del `audit_id` (que ya es
  unico) + `_F` + secuencial con padding de 3 (`F001`, `F010`, `F100`). Asi se garantiza
  unicidad global sin colisiones entre auditorias del mismo activo.
  Ej: audit `plugin_2026-05-31_mi-api` → finding `plugin_2026-05-31_mi-api_F001`.
- `display_id`: `F-NNN`, consecutivo sin saltos. Si se eliminan findings en revision →
  renumerar el display_id (no el finding_id).

---

## Orden en el reporte

Siempre por severidad descendente (**CRITICAL > HIGH > MEDIUM > LOW > INFO**), luego por
`cvss_score` descendente. `F-001` = el mas critico, nunca el orden de descubrimiento.

---

## Campos obligatorios al enviar al gateway

| Campo | Obligatorio | Nota |
|---|---|---|
| `title` | si | lenguaje dev, sin jerga |
| `severity` | si | enum MAYUSCULA |
| `cvss_score` | si | conservador |
| `description` | si | que esta mal y por que es riesgoso |
| `detection_tool` | si | code-review / sqlmap / nuclei / manual |
| `confidence` | si | confirmed/high/medium/low/suspected |
| `evidence.poc_steps` | si | pasos para reproducir |
| `evidence.vulnerable_code` | si (code) | snippet vulnerable |
| `evidence.fix_suggestion` | si (code) | snippet corregido |
| `endpoint` o `source_file` | si | donde esta el problema |

**HTTP 200 NO es confirmacion.** Si no se puede confirmar el efecto real, usar
`confidence: "suspected"`, `dynamic_validation.validated: false` y bajar la severidad un nivel.

---

## Update al cambiar estado (review-loop / review-finding)

```json
{
  "$set": {
    "status": "FIXED",
    "analyst_review": {
      "decision": "CONFIRMED",
      "comment": "Se parametrizo el query con prepared statements en auth.js:45.",
      "reviewed_by": "dev@example.com",
      "reviewed_at": "2026-01-01T00:00:00-05:00"
    },
    "updated_at": "2026-01-01T00:00:00-05:00"
  }
}
```

> El gateway exige una nota (`comment`) de **>= 10 caracteres** para cerrar un finding
> en estados `FIXED`, `FALSE_POSITIVE`, `WONT_FIX` o `ACCEPTED_RISK`.

---

## Update al completar triage

```json
{
  "$set": {
    "triage": {
      "exploitability_score": 8.5,
      "recommended_action": "EXPLOIT_IF_TIME",
      "risk_score": 8.0,
      "scored_at": "2026-01-01T00:00:00-05:00",
      "notes": null
    },
    "cvss_score": 8.2,
    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
    "updated_at": "2026-01-01T00:00:00-05:00"
  }
}
```

---

## Finding de retest (hijo)

```json
{
  "finding_id":        "plugin_mi-api_F001_retest1",
  "display_id":        "F-001",
  "audit_id":          "plugin_2026-05-31_mi-api-retest1",
  "parent_finding_id": "plugin_mi-api_F001",
  "status":            "FIXED",
  "retest_status":     "FIXED",
  "retest_notes":      "El payload original ya no explota; query parametrizado.",
  "analyst_review":    { "decision": "CONFIRMED", "comment": "Retest valida la remediacion.", "reviewed_by": "...", "reviewed_at": "..." }
}
```

Para findings UNFIXED/PARTIAL que se aceptan, completar `retest_justification`.

---

## Ejemplo completo — finding de code review

```json
{
  "finding_id":  "plugin_mi-api_F001",
  "display_id":  "F-001",
  "audit_id":    "plugin_2026-05-31_mi-api",
  "owner":       "local",
  "source":      "developer_plugin",
  "check_id":    "api3_sqli",
  "title":       "SQL Injection en el login",
  "description": "El input del usuario se concatena al query sin sanitizar.",
  "severity":    "CRITICAL",
  "category":    "API3:2023 — Injection",
  "owasp_id":    "API3:2023",
  "affected_resource": "POST /api/users/login",
  "endpoint":    "POST /api/users/login",
  "evidence": {
    "screenshots": [],
    "request":  "POST /api/users/login\n{\"email\":\"a@a.com\",\"password\":\"' OR '1'='1\"}",
    "response": "HTTP/1.1 200 OK\n{\"token\":\"eyJ...\"}",
    "poc_steps": ["Enviar password: ' OR '1'='1", "La API responde con token sin verificar la clave"],
    "technical_analysis": {
      "weak_point": "Input sin sanitizar en el query",
      "root_cause": "Concatenacion directa del input en el query",
      "observed_behavior": "Cualquier password retorna token valido",
      "expected_behavior": "Credenciales invalidas deben rechazarse"
    },
    "remediation": ["Usar prepared statements / queries parametrizados", "Hashear y comparar con bcrypt"],
    "references": ["https://owasp.org/www-project-api-security/"],
    "vulnerable_code": "db.query(`SELECT * FROM users WHERE email='${email}' AND password='${pass}'`)",
    "fix_suggestion": "db.query('SELECT * FROM users WHERE email=$1', [email]); // luego bcrypt.compare"
  },
  "cvss_score":  9.8,
  "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
  "triage": null,
  "dynamic_validation": { "validated": true, "validated_at": "2026-05-31T10:00:00-05:00", "payload_used": "' OR '1'='1", "response_summary": "Token emitido sin clave valida" },
  "status": "OPEN",
  "analyst_review": { "decision": "PENDING", "comment": null, "reviewed_by": null, "reviewed_at": null },
  "parent_finding_id": null,
  "retest_status": null,
  "retest_notes": null,
  "cwe_id": "CWE-89",
  "source_file": "src/controllers/auth.js:45",
  "detection_tool": "code-review",
  "confidence": "confirmed",
  "created_at": "2026-05-31T10:00:00-05:00",
  "updated_at": null
}
```
