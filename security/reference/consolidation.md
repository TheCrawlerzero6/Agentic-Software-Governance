# Flow interno: Consolidación de hallazgos (gating de severidad + fusión por mitigación)

Paso de **finalización** que corre el orquestador ANTES de registrar los findings en el
gateway y ANTES del cierre guiado. Toma los hallazgos crudos que los agentes guardaron
localmente, los hace **honestos** (severidad gateada por impacto real) y los **fusiona por
mitigación**, y recién entonces los registra con `submit_finding`.

> **Por qué aquí:** el gating y la fusión necesitan ver TODOS los hallazgos juntos. Por eso
> los agentes (`pentester-*`, `code-reviewer`) guardan en `audits/{dir}/findings_*.json` y
> emiten `FINDING_DISCOVERED` (progreso), pero NO llaman `submit_finding`: eso lo hace este
> paso tras consolidar. (Los archivos locales dan resistencia a interrupción; si se corta,
> este paso se re-ejecuta desde ellos.)

## Entrada
Todos los `audits/{dir}/findings_*.json` (de los grupos G1/G2/G3 y del code review) y
`directives.json`. Contexto: `audit_id`, `audits/{dir}/`.

## PASO 1 — Investigar las vulnerabilidades por versión (obligatorio)
Para cada hallazgo por **versión/componente** (dependencia/framework/servidor EOL o
desactualizado), invocar:
```
Agent(subagent_type="pentesting-para-desarrolladores:exploit-research",
      prompt="[cve=auto] [source_code_path=...] componente={nombre} version={instalada}
              Busca CVEs + PoC público y confirma si la versión está afectada.")
```
- Versión afectada + PoC público → marcar `cve_ids`, `evidence.references`,
  `confidence: "confirmed"`/`"high"` → cuenta como **impacto demostrado** (no se degrada).
- Sin PoC o versión no confirmada → queda como potencial (se degradará en PASO 2).

## PASO 2 — Severidad por CVSS + gating por impacto real (automático)
La severidad **sale del CVSS** (puedes apoyarte en el agente `cvss-scorer`): score base +
métricas temporales que codifican la confirmación (`E` Exploit Code Maturity, `RC` Report
Confidence). Sin confirmación → `E:U`/`RC:R` bajan el score temporal → baja la severidad.
Sobre eso, aplicar la **política de severidad honesta** de `@reference/rules.md`:

- ¿Impacto demostrado? (`dynamic_validation.validated == true`  **O**  versión afectada +
  PoC público) → **mantener** la severidad.
- Si NO → **degradar** el campo `severity`: `CRITICAL`/`HIGH` → `MEDIUM` (máximo). Marcar:
  - `dynamic_validation.validated = false` (o `null` si no se probó),
  - `confidence` ≤ `"medium"`,
  - en `description`, anotar: "Severidad ajustada a MEDIO: sin impacto demostrado (no
    explotable / no verificado). Severidad teórica original: {orig}".
  - **Mantener `analyst_review.decision = "PENDING"`** (el plugin ajusta la severidad, pero
    la disposición (Confirmada / Falso positivo / Aceptación de riesgo / Fuera de alcance) la
    decide el dev en el review-loop — NO marcar
    como revisado).
- Antes de degradar un candidato fuerte (CRÍTICO/ALTO con indicios claros), intentar
  confirmarlo con `pentester-coder`. Solo si no se confirma, degradar.

## PASO 3 — Fusión automática por mitigación
Agrupar los hallazgos por **mitigación equivalente** (mismo `evidence.fix_suggestion` /
misma `evidence.remediation` / misma `technical_analysis.root_cause`). Para cada grupo de >1:
- Crear UN hallazgo fusionado:
  - `title`: descriptivo del problema común.
  - `affected_resource` / `endpoint`: lista de TODOS los recursos del grupo (o el campo
    `evidence.affected_resources: []` con todos).
  - `evidence`: combinar poc_steps/request-response representativos + el `fix_suggestion` común.
  - `severity`: la **más alta del grupo** (ya gateada en PASO 2).
  - `check_id`/`owasp_id`: el del patrón común.
- No perder trazabilidad: en `evidence` listar cada recurso afectado.

> Ejemplos: 5 endpoints con SQLi por la misma función `buildQuery()` → 1 hallazgo con los 5
> endpoints. 3 endpoints sin rate limiting → 1 hallazgo con los 3. 4 dependencias EOL que se
> arreglan con el mismo `npm update` → 1 hallazgo.

## PASO 4 — Registrar en el gateway
Por cada hallazgo consolidado, `submit_finding` con el modelo rico (ver
`@reference/gateway-persistence.md`). El gateway deriva `finding_id`/`display_id` y valida
el esquema. Renumerar `display_id` por severidad descendente.

## PASO 5 — Resumen al dev
```
🛡️ Consolidación
   Hallazgos crudos: {N}  →  consolidados: {M}  (fusionados por mitigación: {N-M})
   Severidades (honestas): 🔴{crit} 🟠{high} 🟡{med} 🟢{low}
   Degradados por no ser explotables: {k}   (van como "Potencial / requiere verificación")
```
Luego continuar al cierre guiado (`@reference/review-loop.md`), donde el **dev** decide la
disposición final de cada uno (Confirmada / Falso positivo / Aceptación de riesgo / Fuera de alcance).

## Reglas
- Severidad SIEMPRE honesta: nada crítico/alto sin impacto demostrado.
- Fusión automática por mitigación (sin preguntar) — pero conservando todos los recursos en
  la evidencia.
- La degradación la hace el plugin; la **disposición** (Confirmada / Falso positivo /
  Aceptación de riesgo / Fuera de alcance) la decide
  el dev en el review-loop.
