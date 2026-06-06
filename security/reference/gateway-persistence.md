# Cómo guardar datos en el gateway — Plugin para Desarrolladores

> **Guía central de persistencia.** Léela ANTES de llamar a cualquier tool del gateway que
> escriba datos. Los devs NO insertan directo en MongoDB: TODO pasa por las tools MCP del
> `gateway`, que arma el documento y lo guarda. El gateway valida cada documento
> contra un **`$jsonSchema` de MongoDB** (`containers/gateway/init-mongo-schema.js`):
> si los argumentos están incompletos o un enum es inválido, **la escritura se RECHAZA**.

## Fuentes de verdad

| Colección | Esquema (formato exacto) | Tool del gateway que escribe | Validador |
|---|---|---|---|
| `audit_runs` | `@reference/schema/audit_run.md` | `submit_audit`, `submit_event` | `init-mongo-schema.js` |
| `findings` | `@reference/schema/finding.md` | `submit_finding`, `update_finding_review`, `update_finding_triage` | `init-mongo-schema.js` |
| `events` | `@reference/schema/event.md` | `submit_event` (y hooks) | `init-mongo-schema.js` |
| `llm_attack_sessions` | `@reference/schema/llm_attack_session.md` | `submit_llm_session` | `init-mongo-schema.js` |

## Contrato de validación (IMPORTANTE)

El gateway valida ANTES de guardar. Respuestas de error que debes manejar:
- `{"success": false, "error_code": "schema_validation_failed", "detail": "..."}` → el
  documento no cumple el esquema. Lee `detail`, **corrige el campo/enum señalado y reintenta
  la MISMA tool**. NO inventes valores fuera del enum, NO omitas campos obligatorios.
- `{"success": false, "error_code": "invalid_severity" | "invalid_status" | "invalid_audit_type" | ...}`
  → un enum llegó mal. Corrige a un valor válido (ver tablas abajo) y reintenta.
- `{"success": false, "error_code": "review_note_required"}` → faltó la nota ≥10 chars al cerrar.

## Enums válidos (TODOS en MAYÚSCULA salvo `confidence`)

- `severity`: `CRITICAL | HIGH | MEDIUM | LOW | INFO`
- `status` (finding): `OPEN | POTENTIAL | INFORMATIONAL | IN_REVIEW | ACCEPTED_RISK | FIXED | PARTIAL_FIX | WONT_FIX | FALSE_POSITIVE | REOPENED`
- `analyst_review.decision`: `CONFIRMED | OUT_OF_SCOPE | FALSE_POSITIVE | DOWNGRADE | PENDING`
- `retest_status`: `FIXED | PARTIAL | UNFIXED | REGRESSED` (o ausente)
- `recommended_action` (triage): `EXPLOIT_IMMEDIATELY | EXPLOIT_IF_TIME | MONITOR`
- `audit_type`: `APROBACION_ACTIVOS | RETEST_APROBACION`
- `asset_type`: `api | web | web_api | chatbot | n8n_flujo | node_n8n`
- `modality`: `WHITE_BOX | GRAY_BOX | BLACK_BOX | MIXED`
- `confidence` (minúscula): `confirmed | high | medium | low | suspected`
- `status` (audit): `PENDING | IN_PROGRESS | PAUSED | COMPLETED | CANCELLED`

## Mapeo intake → argumentos

| Elección en el intake | Argumento de la tool | Valor |
|---|---|---|
| Proceso "Aprobación de Activos" / "Retest" | `audit_type` | `APROBACION_ACTIVOS` / `RETEST_APROBACION` |
| Tipo de activo (web/api/…/chatbot/workflow/nodo) | `asset_type` | `web` / `api` / `web_api` / `chatbot` / `n8n_flujo` / `node_n8n` |
| Modalidad (Caja Blanca por defecto) | `modality` | `WHITE_BOX` (o GRAY/BLACK) |
| Severidad del hallazgo | `severity` | SIEMPRE MAYÚSCULA |

## Plantillas de argumentos por tool

### `submit_audit` (crea el audit_run)
Obligatorios: `asset_name`, `asset_type`, `target_url`. Recomendados: `audit_type`,
`modality`, `project_name`, `repository_url`, `source_code_path`, `language`, `framework`,
`has_auth`, `skill_name`, `plugin_version`, `client_os`, `started_at`. Retest: `parent_audit_id`,
`retest_number`, `findings_to_retest`.
> El gateway pone `audit_id`, `owner`, fechas, `status`, `severities`, `findings_count`.
> No los mandes tú. `target_url` debe ser localhost / RFC1918 / dominio permitido (scope).

### `submit_finding` (crea un finding — modelo rico)
Obligatorios: `audit_id`, `title`, `severity` (MAYÚSCULA). Fuertemente recomendados:
`check_id`, `owasp_id`, `category`, `endpoint` o `source_file`, `description`,
`detection_tool`, `confidence`, y `evidence` con `poc_steps`, `technical_analysis`,
`vulnerable_code`/`fix_suggestion` (code review), `dynamic_validation` (`validated` true/false/null).
> El gateway deriva `finding_id = {audit_id}_F{NNN}`, `display_id`, e inicializa
> `status=OPEN` + `analyst_review.decision=PENDING`. No mandes `finding_id`.

### `update_finding_review` (cerrar/clasificar un finding)
Obligatorios: `finding_id`, `status`. Opcional: `decision`, `review_note`, `retest_status`.
> `review_note` ≥10 chars es OBLIGATORIA para `FIXED`, `FALSE_POSITIVE`, `WONT_FIX`,
> `ACCEPTED_RISK`. Ver tabla de traducción amigable↔enum en `@reference/review-loop.md`.

### `update_finding_triage` (priorización)
Obligatorios: `finding_id`, `recommended_action`. Opcional: `exploitability_score`,
`risk_score`, `notes`, `cvss_score`, `cvss_vector`.

### `submit_event` (telemetría / ciclo de vida)
Obligatorio: `event_type` (MAYÚSCULA canónico — ver `event.md`). Para `AUDIT_COMPLETED`
incluir `findings_count`, `severities` (5 claves minúscula), `duration_seconds`. Un
`event_type` no canónico se acepta pero se marca `deprecated_schema` automáticamente.

### `submit_llm_session` (solo chatbot)
Obligatorios: `session_id`, `audit_id`. Recomendados: `channel`, `mode`, `language`,
`status` (`IN_PROGRESS|COMPLETED|PAUSED|CANCELLED`), y el objeto `session` con el resto.

## Reglas críticas
- `severity` y `status` SIEMPRE en MAYÚSCULA. `confidence` en minúscula.
- Las **fechas las pone el gateway** — el LLM no manda `created_at`/`updated_at`.
- En code review, `evidence.vulnerable_code` y `evidence.fix_suggestion` son obligatorios.
- Si una tool devuelve `schema_validation_failed`/`invalid_*`, **corrige y reintenta** — no
  continúes como si hubiera guardado.
- El registro es obligatorio: sin `audit_id` válido del gateway no se puede continuar la auditoría.
