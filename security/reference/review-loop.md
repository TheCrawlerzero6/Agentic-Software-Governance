# Flow interno: Cierre guiado de findings (triage + fix)

Flow reutilizable que recorre los findings de una auditoría hasta dejarlos todos en estado
terminal. Se invoca con un `audit_id` como contexto desde:

- `reference/pentest-app.md` (al terminar el pentest)
- `reference/code-review.md` (al terminar el code review)
- `reference/n8n-audit.md` / `n8n-node-review.md` (al terminar la auditoría n8n)
- `reference/pentest-chatbot.md` (al terminar la auditoría del bot)
- `reference/retest-app.md` (cierre del retest)
- `commands/mis-auditorias.md` ("Revisar findings pendientes")

## Regla crítica

UNA vulnerabilidad a la vez. Esperar respuesta del dev antes de pasar a la siguiente.
**Nunca** exponer los enums crudos del modelo (`OPEN`, `FIXED`, `CONFIRMED`,
`FALSE_POSITIVE`, `WONT_FIX`, `OUT_OF_SCOPE`, `ACCEPTED_RISK`, `PENDING`) en mensajes al
dev — usar siempre los nombres amigables de la tabla de traducción.

### Prohibiciones anti-batch (OBLIGATORIO)
- **PROHIBIDO** mostrar un listado/resumen de todos los findings y pedir clasificación por
  lotes ("responde F001 confirmada, F002 falso positivo"). Cada finding se presenta uno por
  uno con su tarjeta completa.
- **PROHIBIDO** listar las categorías de clasificación (Confirmada / Falso positivo / etc.)
  sin ANTES haber mostrado la tarjeta completa del finding actual.
- **PROHIBIDO** preguntar "¿quieres revisarlas una por una o por lotes?". Siempre es una por una.
- **OBLIGATORIO** que la intro de FASE 1 y la tarjeta del PRIMER finding vayan en el MISMO
  mensaje — el dev NUNCA debe ver solo la intro sin un finding concreto debajo.

## Traducción de estados (única fuente de verdad)

El modelo del servidor es rico: el estado vive en `status` (ciclo de vida) +
`analyst_review.decision` (juicio del analista). El dev solo ve nombres amigables.
Esta tabla la consumen también `review-finding.md` y `mis-auditorias.md`.

| Nombre amigable (al dev) | `status` | `analyst_review.decision` | ¿Comentario ≥10? | Sinónimos que se aceptan como input |
|---|---|---|---|---|
| **Sin clasificar** | `OPEN` | `PENDING` | no | "sin clasificar", "pendiente" |
| **Confirmada** | `OPEN` | `CONFIRMED` | no | "confirmada", "es real", "sí existe" |
| **Corregida** | `FIXED` | `CONFIRMED` | **sí** | "corregida", "arreglado", "ya lo arreglé" |
| **Falso positivo** | `FALSE_POSITIVE` | `FALSE_POSITIVE` | **sí** | "falso positivo", "fp", "comportamiento esperado" |
| **Aceptación de riesgo** | `ACCEPTED_RISK` | `CONFIRMED` | **sí** | "acepto el riesgo", "asumo el riesgo", "riesgo aceptado" |
| **Fuera de alcance** | `WONT_FIX` | `OUT_OF_SCOPE` | **sí** | "fuera de alcance", "otro componente", "no es mío", "no lo administro" |

Significado de los tres estados de no-corrección (el dev SIEMPRE deja un comentario):
- **Falso positivo** — es comportamiento esperado de la aplicación; no es una vulnerabilidad.
- **Aceptación de riesgo** — es real, pero el área dueña del aplicativo asume la
  responsabilidad de dejarla sin mitigar.
- **Fuera de alcance** — corresponde a un componente distinto que el dev no administra.

Reglas:
- **Output:** nunca imprimir el enum crudo. Siempre el nombre amigable.
- **Input por número:** menús numerados con el nombre amigable; el dev elige "1/2/3/4".
- **Input por texto libre:** normalizar con la tabla de sinónimos. Sin match único → mostrar
  el menú numerado.
- La tool `update_finding_review` exige `review_note` ≥10 chars para `FIXED`,
  `FALSE_POSITIVE`, `WONT_FIX` y `ACCEPTED_RISK` (es decir, los tres estados de no-corrección
  y el de corregida). "Confirmada" (status OPEN) no exige comentario.

## Setup

```
mcp__gateway__get_audit_findings({"audit_id": <audit_id>})
```

Particionar (un hijo de retest con `retest_status == "FIXED"` se considera **cerrado**, aunque
su `status` siga `OPEN` — el retest ya lo verificó; no entra al triage):
- `closed    = {f | f.status ∈ {"FIXED","FALSE_POSITIVE","WONT_FIX","ACCEPTED_RISK"}  ó  f.retest_status == "FIXED"}`
- `to_triage = {f | f ∉ closed y f.analyst_review.decision == "PENDING"}`
- `to_fix    = {f | f ∉ closed y f.status == "OPEN" y f.analyst_review.decision == "CONFIRMED"}`

**Si `to_triage` y `to_fix` están vacíos:** mostrar resumen y retornar sin entrar al loop.
**Si `to_triage` está vacío pero `to_fix` no:** saltar directo a FASE 2.

## FASE 1 — Triage

Ordenar `to_triage` por severidad (CRITICAL→INFO), luego `cvss_score` desc.

**La intro y la tarjeta del PRIMER finding van en el mismo mensaje** (el dev nunca ve solo
la intro). Formato:

```
Revisemos {|to_triage|} vulnerabilidades (de la más grave a la menos). Empezamos:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{display_id} · {emoji} {SEVERIDAD} (CVSS {score}) · {🟥 EXPLOTABLE | ⬜ NO EXPLOTABLE}
…(tarjeta completa)…
```

**Por cada finding (UNA pregunta a la vez).** La tarjeta es **fiel al reporte**: mismos
campos que `agents/reporter.md` (título, afectados, badge explotable, severidad+CVSS,
descripción, evidencia/PoC, **escenario de ataque**, recomendación). El detalle del fix
concreto se guía DESPUÉS, solo si el dev la marca Confirmada (FASE 2).

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{display_id} · {emoji} {SEVERIDAD} (CVSS {score}) · {🟥 EXPLOTABLE | ⬜ NO EXPLOTABLE}

{title}

Afectados:
  • {endpoint o source_file 1}   ({parámetro/detalle si aplica})
  • {endpoint o source_file 2}   ...        (lista TODOS los recursos fusionados)

Descripción
  {qué está mal y por qué importa, en lenguaje dev — 2-3 oraciones}

Evidencia / prueba de concepto
  {payload usado · request/response resumido · o comportamiento observado}

Código vulnerable ({source_file}:{línea})        (si aplica)
```{language}
{evidence.vulnerable_code}
```

Escenario de ataque
  Flujo normal (comportamiento esperado)
  1. {paso 1 del uso legítimo}
  2. {paso 2}
  …

  Flujo del atacante (cómo se aprovecha)
  1. {paso 1 del atacante}
  2. {paso 2 — aquí se explota la debilidad}
  …

  Impacto concreto
  Un atacante con {qué necesita: JWT válido, acceso a la red, cédula…} puede:
  - {consecuencia 1}
  - {consecuencia 2}

Recomendación de mitigación
  {evidence.fix_suggestion en 1-2 oraciones; el diff concreto se aplica en FASE 2}
```
- Badge EXPLOTABLE/NO sale de `dynamic_validation.validated` (true/false; `null` → sin badge).
- "Afectados" lista TODOS los recursos del hallazgo fusionado (de `evidence.affected_resources`).
- Si es hallazgo por versión/CVE: en Evidencia mostrar `cve_ids` + enlace al PoC público.
- **Escenario de ataque**: OBLIGATORIO. Se construye a partir de `evidence.poc_steps`,
  `evidence.request/response`, `evidence.vulnerable_code` y `evidence.technical_analysis`.
  Debe ser **específico al hallazgo** (no genérico OWASP). El "flujo normal" muestra cómo
  funciona la app correctamente; el "flujo del atacante" muestra paso a paso cómo se bypasea
  o explota; el "impacto concreto" lista qué necesita el atacante y qué logra.

Pregunta:
```
¿Cómo la clasificas?
1. Confirmada — es real, la voy a corregir
2. Falso positivo — es comportamiento esperado de la app
3. Aceptación de riesgo — es real, mi área asume el riesgo de no mitigarla
4. Fuera de alcance — corresponde a otro componente que no administro
5. Conversar — tengo dudas, quiero entender mejor o no estoy de acuerdo
```

**Opción 1 — Confirmada** (no pide comentario; se llena al corregir en FASE 2):
```
mcp__gateway__update_finding_review({
  "finding_id": "<finding_id>", "status": "OPEN", "decision": "CONFIRMED", "review_note": ""
})
```
Pasa al pool de FASE 2.

**Opción 5 — Conversar:** se abre una conversación libre sobre ESTE finding. No hay límite
de turnos. El dev puede:
- Preguntar sobre la vulnerabilidad (cómo funciona, por qué importa, qué riesgo real tiene).
- Discutir el **escenario de ataque** (pedir más detalle, cuestionar un paso).
- Discutir la **sugerencia de mitigación** (proponer alternativa, preguntar si su enfoque es
  correcto, entender por qué ese fix y no otro).
- **Argumentar que no es vulnerable** — aquí el plugin evalúa el argumento contra la
  evidencia (request/response, código, PoC, CVE, escenario de ataque):
  - Si el argumento es válido (hay un control no detectado, el endpoint no es alcanzable, el
    parámetro está sanitizado por un middleware oculto, el comportamiento es intencionado) →
    el plugin acepta y **sugiere Falso positivo** con el motivo como comentario.
  - Si el argumento **no se sostiene** (la evidencia lo contradice) → el plugin explica con
    claridad por qué SÍ es vulnerable, mostrando la evidencia concreta (payload que funcionó,
    respuesta del servidor, línea de código donde ocurre), y re-presenta el menú.

**Salir de la conversación:** cuando el dev dice "ok", "entendido", "listo", o elige
directamente una opción (1-4), se re-presenta el menú de clasificación. El plugin **no cambia
la clasificación automáticamente**: siempre vuelve al menú para que el dev confirme.

> **Opciones 2, 3 y 4: comentario SIEMPRE obligatorio (≥10 chars).** Hacer la pregunta
> adecuada, insistir si <10. **Antes de persistir**, pasar por el *Asistente de coherencia*.

Pregunta del comentario según la opción elegida:
- **2. Falso positivo:** "¿Por qué es comportamiento esperado de la app? (mín. 10 caracteres)"
- **3. Aceptación de riesgo:** "¿Qué área asume el riesgo y por qué? (mín. 10 caracteres)"
- **4. Fuera de alcance:** "¿A qué componente o equipo corresponde? (mín. 10 caracteres)"

### Asistente de coherencia (antes de guardar opciones 2/3/4)

Con el comentario en mano, evaluar dos cosas del finding:
- **demostrado** = `severity ∈ {CRITICAL, HIGH}` (por la política de severidad honesta, un
  crít/alto ya tiene impacto demostrado: explotación confirmada o CVE+PoC público).
- **capa** = **INFRA** si el hallazgo es de servidor / protocolo / TLS / certificado /
  configuración de plataforma **no administrada por el dev** (pistas: sin `source_file` del
  repo; título/categoría sobre TLS, cifrado de transporte, cabeceras del servidor, versión
  del servidor web, certificado); en caso contrario **APP** (código o dependencia del dev).

Aplicar, en orden:

1. **⛔ BLOQUEO (escenario 4)** — si el dev eligió **Falso positivo**, o **Fuera de alcance**
   con `capa == APP`, sobre un finding **demostrado** → NO persistir esa clasificación.
   Mostrar el bloque **"Bloqueo escenario 4"** (abajo) y re-decidir.

2. **💡 Sugerir Confirmada** — si eligió **Aceptación de riesgo** pero el comentario indica que
   se va a corregir/postergar ("lo arreglo", "se mitiga al subir a producción", "temporal",
   "en el próximo sprint"):
   ```
   Eso no es aceptar el riesgo, es posponer la corrección: la vulnerabilidad seguiría real y
   abierta. ¿La dejamos como "Confirmada" para corregirla (ahora o luego)?
   1. Sí, Confirmada    2. No, mantener Aceptación de riesgo
   ```

3. **💡 Sugerir Fuera de alcance** — si eligió **Aceptación de riesgo** pero el comentario
   describe un componente/equipo externo o infra que no administra:
   ```
   Por lo que describes, esto no lo administras tú; encaja mejor como "Fuera de alcance".
   1. Sí, Fuera de alcance    2. No, mantener Aceptación de riesgo
   ```

Si no aplica ningún bloqueo/sugerencia (o el dev mantiene su elección permitida), persistir
con el mapeo de abajo.

### Persistir (según la categoría final)

| Categoría final | `status` | `decision` |
|---|---|---|
| Falso positivo | `FALSE_POSITIVE` | `FALSE_POSITIVE` |
| Aceptación de riesgo | `ACCEPTED_RISK` | `CONFIRMED` |
| Fuera de alcance | `WONT_FIX` | `OUT_OF_SCOPE` |
```
mcp__gateway__update_finding_review({
  "finding_id": "<finding_id>", "status": "<status>",
  "decision": "<decision>", "review_note": "<comentario>"
})
```

### Bloqueo escenario 4 (crít/alto que no se puede descartar)

```
⛔ No puedo marcar esta vulnerabilidad {CRÍTICA/ALTA} como "{Falso positivo | Fuera de alcance}".
Razón: se validó que es un problema REAL con impacto demostrado
({explotación confirmada | PoC público y tu versión está en el rango afectado}).
Una vulnerabilidad de esta severidad y con evidencia no es comportamiento normal ni de otro
componente — está en tu código o en una dependencia demasiado obsoleta que tú administras.

¿Qué hacemos?
1. Corregirla — te guío en el fix (Confirmada)
2. Aceptación de riesgo — tu área asume formalmente el riesgo (la auditoría quedará CON CONDICIONES)
3. Redactar correo para tu equipo de seguridad — soporte, o si crees que es un error de la herramienta
```
- **1** → persistir Confirmada (`OPEN`/`CONFIRMED`), pasa a FASE 2.
- **2** → pedir comentario del área que asume el riesgo (≥10) y persistir Aceptación de riesgo.
- **3** → **Redactar correo** (no se envía): mostrarlo listo para copiar.
  ```
  Para: tu equipo de seguridad
  Asunto: [Pentesting plugin] Revisión de hallazgo {display_id} — {audit_id}

  Hola equipo de seguridad,

  Durante una auditoría de Aprobación de Activos con el plugin de pentesting, no puedo
  cerrar el siguiente hallazgo y solicito su revisión/soporte:

  - Auditoría: {audit_id}
  - Hallazgo: {display_id} — {title}
  - Severidad: {severidad} (CVSS {score})
  - Afectados: {recursos/endpoints}
  - Evidencia: {resumen de la PoC / cve_ids + PoC público}
  - Motivo que indico: {comentario del dev}

  Quedo atento. Gracias.
  {dev}
  ```
  Tras mostrarlo, el finding **sigue pendiente** (no se cierra) hasta que el dev lo corrija o
  acepte el riesgo, o el equipo de seguridad intervenga. Continuar con el siguiente finding.

**Tras cada acción (nombre amigable):**
```
✓ {display_id}: {Confirmada | Falso positivo | Aceptación de riesgo | Fuera de alcance}
   Quedan {restantes en triage} por clasificar.
```

Al terminar, recalcular `to_fix = {f | status=="OPEN" y decision=="CONFIRMED"}`.

## Transición FASE 1 → FASE 2
```
Triage completado.
   ✓ Confirmadas (a corregir):  {|to_fix|}
   ⊘ Falsos positivos:          {|false_positive|}
   ⚠ Riesgo aceptado:           {|accepted_risk|}
   ↗ Fuera de alcance:          {|out_of_scope|}
```
Si `|to_fix| == 0` → ir al **Cierre**.

## FASE 2 — Fix

Intro (breve):
```
Corrijamos las {|to_fix|} confirmadas. Para cada una te propongo un fix; tú decides.
```

**Por cada finding en `to_fix` (UNA pregunta a la vez):**

Generar la sugerencia: si `evidence.fix_suggestion` existe, usarla; si no, leer
`source_file` alrededor de la línea con Read y proponer un fix según lenguaje/OWASP.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fix {N}/{|to_fix|} · {display_id} · {emoji} {severidad amigable}
{title}   📁 {source_file}

Código actual:
```{language}
{snippet leído del archivo}
```
Sugerencia de corrección:
```{language}
{evidence.fix_suggestion o snippet propuesto}
```
¿Por qué este fix? {1-2 oraciones}
```

Pregunta:
```
¿Qué hacemos?
1. Aplicar la sugerencia tal cual
2. Aplicar con cambios míos (te dicto)
3. Yo lo arreglo a mano
4. Pedir otra sugerencia
5. Saltar por ahora (sigue como Confirmada)
6. Conversar — quiero entender mejor esta corrección
```

**Opción 1 — Aplicar tal cual:** Edit en `source_file`, mostrar diff, confirmar
"¿Quedó bien? (sí/no)". Si sí:
```
mcp__gateway__update_finding_review({
  "finding_id": "<finding_id>", "status": "FIXED", "decision": "CONFIRMED",
  "review_note": "Fix aplicado por el plugin: <descripción del cambio>"
})
```
Si no: volver a la pregunta (no avanzar).

**Opción 2 — Aplicar con cambios:** pedir ajustes, generar snippet ajustado, Edit, diff,
marcar `FIXED` con nota "Fix aplicado con ajustes del dev: <resumen>".

**Opción 3 — A mano:** pedir nota (≥10 chars: commit/PR, función, sanitización aplicada),
insistir si <10, marcar `FIXED` con la nota del dev.

**Opción 4 — Otra sugerencia:** regenerar con enfoque distinto y re-preguntar.

**Opción 5 — Saltar:** continuar; queda Confirmada (status OPEN, decision CONFIRMED).

**Opción 6 — Conversar:** conversación libre sobre el fix propuesto. El dev puede preguntar
por qué ese enfoque, proponer alternativa, discutir si es suficiente, etc. El plugin responde
técnicamente. Al terminar ("ok", "listo", o elige 1-5), re-presentar el menú de fix.

**Tras cada acción 1-3:**
```
✓ {display_id}: Corregida
   Quedan {restantes en fix} por corregir.
```

## Cierre

Recalcular contadores.

**Si todo cerrado (sin PENDING ni Confirmadas-OPEN):**
```
Revisión completada.
   ✓ Corregidas:        {|FIXED|}
   ⊘ Falsos positivos:  {|FALSE_POSITIVE|}
   ⚠ Riesgo aceptado:   {|ACCEPTED_RISK|}
   ↗ Fuera de alcance:  {|WONT_FIX+OUT_OF_SCOPE|}
```

**Si quedaron pendientes:**
```
Pausaste la revisión.
   ✓ Corregidas:                {|FIXED|}
   ⊘ Falsos positivos:          {|FALSE_POSITIVE|}
   ⚠ Riesgo aceptado:           {|ACCEPTED_RISK|}
   ↗ Fuera de alcance:          {|WONT_FIX+OUT_OF_SCOPE|}
   🔧 Confirmadas sin corregir:  {confirmadas OPEN}
   ⏳ Sin clasificar:            {PENDING}
Para retomar: /mis-auditorias → "Revisar findings pendientes".
```

Retornar al caller con los contadores (incluyendo `|FIXED|`) para que decida qué ofrecer
después (p. ej. sugerir el **retest** si hubo correcciones — lo maneja el caller, no este flow).

## Telemetría

`update_finding_review` emite `FINDING_REVIEWED` desde el servidor. Este flow no emite
eventos adicionales.

## Reglas
- UNA vulnerabilidad a la vez (ver prohibiciones anti-batch). Nunca apilar opciones de
  varios findings. La intro + primera tarjeta van en el mismo mensaje.
- Nunca imprimir enums crudos; usar nombres amigables.
- SIEMPRE incluir el **Escenario de ataque** (flujo normal vs. flujo del atacante + impacto
  concreto) en cada tarjeta. Es lo que le da sentido al hallazgo para el dev.
- Comentario obligatorio ≥10 chars en Corregida, Falso positivo, Aceptación de riesgo y
  Fuera de alcance (los tres de no-corrección siempre llevan el motivo).
- **Escenario 4:** un CRÍTICO/ALTO con impacto demostrado NO se puede marcar Falso positivo,
  ni Fuera de alcance cuando es código/dependencia propia → el plugin bloquea y ofrece
  corregir / aceptar riesgo / correo a `tu equipo de seguridad`. "Fuera de alcance" SÍ es
  válido para hallazgos de servidor / protocolo / certificado que el dev no administra.
- Tras el comentario de no-corrección, correr el **Asistente de coherencia** y sugerir la
  categoría que mejor encaje (p. ej. "lo arreglo en prod" → Confirmada, no Aceptación de riesgo).
- Directo, sin palabrería; el detalle se reserva para descripción, evidencia y mitigación.
- Si el dev cancela a mitad: cierre por pausa; cada `update_finding_review` ya está persistido.
- Idioma: Español, tono cercano, sin jerga.
