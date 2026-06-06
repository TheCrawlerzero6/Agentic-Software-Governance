# Skill: N8N Workflow Audit

## Cuando activar

El analista menciona: "n8n", "workflow n8n", "auditar workflow", "revisar n8n", "seguridad n8n",
"analisis de workflow", "revisar JSON de n8n", "auditoria n8n".

**Modo hibrido:** Tambien se activa como parte de `pentest-app` cuando el analista provee
workflow JSON durante un pentesting web. En ese caso, el skill principal orquesta la ejecucion
y NO se sigue este flujo de intake — los datos del reporte y nombre del activo
ya fueron recopilados por el intake.

## Fase 1 — Clarificacion

Preguntar UNA a la vez, en este orden:

**Paso 1 — JSON del workflow:**
```
Vamos con la auditoría del workflow n8n.

Comparte el JSON del workflow:
  - Puedes pegarlo directamente
  - O indica la ruta del archivo .json
```

**Paso 2 — Nombre del activo:**
```
Nombre del sistema o activo al que pertenece este workflow?
(Ej: "DjBot", "Autosoporte ACME", "Pipeline de facturación")
```

**Paso 3 — Datos del reporte:**
```
Datos para el registro de auditoría:
  - Autor (tu usuario)
  - QA (quien revisara)
  - Destinatario (a quien va dirigido)
  - Departamento
  - Proyecto
```

## Fase 2 — Plan

Mostrar antes de ejecutar:

```
PLAN DE AUDITORÍA N8N
━━━━━━━━━━━━━━━━━━━━━
Workflow: {nombre}
Activo: {activo}
Tipo: Análisis estático de seguridad
Tier: 1 (análisis estático, sin ejecución activa)

Áreas a revisar:
  SEC-1  Credenciales y secretos hardcodeados
  SEC-2  Nodos de ejecución de alto riesgo
  SEC-3  Seguridad de webhooks y triggers
  SEC-4  Inyección de prompts y riesgos de agentes IA
  SEC-5  SQL injection en queries manuales
  SEC-6  Datos en tránsito y logs

Empiezo? (si/no)
```

Registrar en gateway al confirmar.

## Fase 3 — Analisis

Leer el JSON completo. Mostrar checklist con progreso después de cada área:

```
[x] SEC-1 Credenciales     — LIMPIO
[x] SEC-2 Ejecución        — LIMPIO
[x] SEC-3 Webhooks         — 1 hallazgo
[ ] SEC-4 IA               — EN PROGRESO
[ ] SEC-5 SQL              — PENDIENTE
[ ] SEC-6 Tránsito/Logs    — PENDIENTE
```

### SEC-1: Credenciales y Secretos Hardcodeados

Buscar en todos los campos de parámetros de nodos:
- Strings que parezcan tokens/keys: largos, aleatorios, con prefijos `sk-`, `Bearer `, `token=`, `api_key=`, `password=`, `secret=`
- Credenciales válidas en n8n aparecen como `{"id": "...", "name": "..."}` en el campo `credentials`. Si el valor es un string directo → hallazgo crítico.

### SEC-2: Nodos de Ejecución de Alto Riesgo

Buscar:
- Nodos de tipo `n8n-nodes-base.executeCommand` activos sin Sticky Note de justificación
- Nodos `Code` (`n8n-nodes-base.code`) que tomen input del usuario y lo pasen a `exec`, `spawn`, `child_process`, o `eval`

### SEC-3: Seguridad de Webhooks y Triggers

Buscar:
- Nodos `n8n-nodes-base.webhook` sin autenticación en los parámetros (`authentication` ausente o `none`)
- Ausencia de nodos IF que validen campos obligatorios de la request antes de procesarla
- Nodos `chatTrigger` con `"public": true` sin ningún control de acceso posterior en el flujo

### SEC-4: Inyeccion de Prompts y Riesgos de Agentes IA

Aplica solo si hay nodos `agent`, `lmChat` u otros de LangChain (`@n8n/n8n-nodes-langchain.*`).

**a) Filtro de prompt injection solo con keywords estáticas:**
Si el workflow usa un nodo `Code` con listas de palabras bloqueadas para proteger al agente, es bypassable. La corrección es un nodo LLM clasificador semántico separado + delimitadores explícitos en el system prompt (`<user_input>...</user_input>`).

**b) Herramientas del agente con match por campo único controlado por el usuario:**
Si un nodo `postgresTool`, `mysqlTool` o similar usa `$fromAI(...)` como único criterio en `WHERE` o `matchingColumns`, un atacante que manipule al agente puede apuntar UPDATE/DELETE a registros de otros usuarios. Corrección: anclar la operación a un segundo campo que el usuario no controla (ej: `session_id`, timestamp de sesión, o ID interno del audit_run).

**c) System prompt con arquitectura interna:**
Nombres de tablas, herramientas, rutas o credentials dentro del system prompt quedan expuestos en el JSON exportado. Si hay instrucciones sensibles, separarlas a un nodo de configuración con acceso restringido.

**d) Herramientas ejecutables directamente por instrucción del usuario:**
Si el system prompt no tiene restricción explícita de que solo el flujo autoriza el uso de herramientas, un atacante puede instruir al agente para que las invoque directamente.

> **Hallazgos encadenados:** Si hay bypass de filtro (SEC-4a) Y herramienta con match único (SEC-4b), reportar SEC-4a como el hallazgo principal y mencionar que SEC-4b es explotable a través de él. Priorizar corregir SEC-4a.

### SEC-5: SQL Injection en Queries Manuales

Aplica solo a nodos con queries escritas a mano (`executeQuery`). Verificar:
- Valores dinámicos usan parámetros posicionales (`$1`, `$2`) — NO interpolación de strings
- Queries destructivas (`DELETE`, `DROP`, `TRUNCATE`) tienen validación estricta de parámetros de entrada

### SEC-6: Datos en Transito y Logs

Buscar:
- URLs en nodos HTTP Request con `http://` en lugar de `https://`
- Nodos `Code` con `console.log` que impriman tokens, passwords o datos personales
- Campos `debug_*` con contenido sensible que persistan en producción

## Fase 4 — Consolidación + resultados

El agente `pentester-n8n` guardó los hallazgos en `audits/{dir}/findings_n8n.json` (sin
registrarlos). Seguir `@reference/consolidation.md`: gatear severidad por impacto real
(análisis estático → potencial; no marcar crítico/alto sin confirmar, salvo versión con
CVE+PoC), fusionar por mitigación, y registrar con `submit_finding`. Luego mostrar:

```
AUDITORÍA N8N COMPLETADA
━━━━━━━━━━━━━━━━━━━━━━━━
Workflow: {nombre}
Hallazgos (severidades honestas): N (X Critical, X High, X Medium, X Low)
```

## Fase 5 — Cierre guiado de findings (obligatorio si hay hallazgos)

**Si hay 0 hallazgos:** saltar a Fase 6.

**Si hay hallazgos:** entrar automáticamente al loop guiado siguiendo las
instrucciones de `@reference/review-loop.md` con el `audit_id` actual.

En FASE 2 del loop, cuando se trate de hallazgos n8n el "fix" no es Edit en
código del repo: la corrección vive en el JSON del workflow (cambiar el
parámetro de un nodo, agregar autenticación al webhook, etc.). Adaptar la
opción 1/2 del fix para mostrar el cambio recomendado en el JSON sin
ejecutarlo automáticamente — el dev lo aplica en su instancia n8n y luego
selecciona opción 3 ("yo lo arreglo a mano") con la nota de qué cambió.

## Fase 6 — Menú post-revisión

```
Qué deseas hacer?
1. Ver resumen ejecutivo en chat
2. Generar informe Markdown
3. Hacer triage (priorizar correcciones)
4. Nada por ahora
```

## Formato de findings

Usar el schema estándar del plugin con estas adaptaciones para n8n:

```json
{
  "finding_id": "plugin_{workflow-slug}_F001",
  "display_id": "F-001",
  "audit_id": "{audit_id}",
  "source": "developer_plugin",
  "check_id": "n8n_sec{N}_{tipo}",
  "title": "{titulo del hallazgo}",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
  "category": "n8n SEC-{N} — {nombre del area}",
  "affected_resource": "{nombre del nodo afectado}",
  "description": "{descripcion del hallazgo}",
  "cvss_score": null,
  "cvss_vector": null,
  "status": "OPEN",
  "evidence": {
    "sec_id": "SEC-{N}",
    "node_name": "{nombre exacto del nodo}",
    "field": "{campo o parametro afectado}",
    "poc_steps": ["Paso 1...", "Paso 2..."],
    "technical_analysis": {
      "weak_point": "{que es vulnerable}",
      "root_cause": "{causa raiz}",
      "observed_behavior": "{que se observo en el JSON}",
      "expected_behavior": "{configuracion correcta esperada}"
    },
    "remediation": ["Correccion concreta dentro de n8n..."],
    "references": []
  },
  "created_at": "{ISO timestamp}"
}
```

**Patrones de `check_id`:**

| Hallazgo | check_id |
|----------|----------|
| Credencial hardcodeada | `n8n_sec1_hardcoded_credential` |
| Execute Command sin justificación | `n8n_sec2_execute_command` |
| Code node con ejecución de input | `n8n_sec2_code_exec_input` |
| Webhook sin autenticación | `n8n_sec3_webhook_no_auth` |
| Sin validación de input en webhook | `n8n_sec3_no_input_validation` |
| Filtro de prompt injection bypassable | `n8n_sec4_prompt_injection_filter` |
| Herramienta con match por campo único | `n8n_sec4_tool_single_field_match` |
| System prompt con arquitectura interna | `n8n_sec4_system_prompt_exposure` |
| Herramienta ejecutable por usuario | `n8n_sec4_tool_user_invocable` |
| SQL injection por interpolación | `n8n_sec5_sqli_interpolation` |
| Query destructiva sin validación | `n8n_sec5_destructive_query` |
| HTTP sin HTTPS | `n8n_sec6_http_no_tls` |
| console.log con datos sensibles | `n8n_sec6_console_log_sensitive` |

## Registro en Gateway

Usar las tools del gateway (no MongoDB directo). El análisis SEC puede delegarse al agente
`pentester-n8n` (modo workflow), que ya contiene el detalle SEC-1..6.

### Al confirmar el plan — registrar la auditoría:
```
mcp__gateway__submit_audit({
  "asset_name": "{nombre del activo}",
  "asset_type": "n8n_flujo",
  "audit_type": "APROBACION_ACTIVOS",
  "modality": "WHITE_BOX",
  "target_url": "host.docker.internal",   // estático: el workflow no es un servicio con URL
  "project_name": "{proyecto}", "repository_url": "{repo}",
  "skill_name": "n8n-audit", "plugin_version": "...", "client_os": "...", "started_at": "..."
})
```

### Al guardar cada hallazgo — `submit_finding`:
Usar el modelo rico de `@reference/schema/finding.md` (severity MAYÚSCULA, status OPEN,
analyst_review PENDING). Para n8n: `evidence.sec_id` (ej. "SEC-4b") y `evidence.node_name`.

### Al completar — emitir el evento (el dictamen lo calcula el servidor):
```
mcp__gateway__submit_event({
  "audit_id": "{audit_id}", "event_type": "AUDIT_COMPLETED",
  "findings_count": N, "severities": {"critical":0,"high":1,"medium":1,"low":0,"info":0},
  "duration_seconds": <int>
})
```
El servidor calcula el `dictamen` (SE APRUEBA / CON CONDICIONES / NO SE APRUEBA) a partir
del estado de los findings. No calcularlo en el plugin.

Emitir también `AUDIT_STARTED` lo gestiona `submit_audit`; el cierre guiado y el reporte
siguen como en `pentest-app.md`.

## Reglas

- Lee el JSON con Read, NO ejecutes el workflow
- Análisis estático únicamente — Tier 1, sin herramientas activas
- Solo reporta hallazgos con corrección accionable dentro de n8n
- No sugerir variables de entorno (`$env.*`) como corrección
- No reportar separación de credenciales como hallazgo
- No reportar riesgos que solo se mitigan en infraestructura externa
- Preguntas SIEMPRE una por una
- Cada hallazgo: nombre del nodo, campo exacto, snippet del valor problemático (ofuscar tokens con `[REDACTED]`)
- Evalúa el contexto del flujo completo antes de clasificar severidad (ej: webhook público en chatbot puede ser intencional)
- Timezone: UTC
- Idioma: Español
