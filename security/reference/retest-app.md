# Flow interno: Retest de Aprobación de Activos

Se invoca cuando el dev elige **Retest** (proceso `RETEST_APROBACION`). Re-verifica los
findings de una auditoría original ya cerrada para confirmar que las correcciones funcionan,
y emite un dictamen actualizado con la tendencia del riesgo.

## FASE 1 — Elegir la auditoría original
```
mcp__gateway__get_audits({"limit": 20, "status": "COMPLETED"})
```

**Guard — sin auditorías previas:** si la lista viene **vacía** (el dev no tiene ninguna
auditoría COMPLETED suya), NO se puede retestear (no hay nada que re-verificar). Mostrar y
ofrecer arrancar una auditoría nueva, sin quedar colgado:
```
No tienes auditorías previas completadas para retestear.
Un retest re-verifica las correcciones de una auditoría anterior, así que primero necesitas
correr una Aprobación de Activos.

¿Quieres iniciar una Aprobación de Activos ahora?
1. Sí, auditar mi aplicación    2. No, salir
```
- Opción 1 → seguir `@reference/pentest-app.md` (rama Aprobación de Activos) y terminar aquí.
- Opción 2 → terminar.

Si hay ≥1: mostrar las auditorías COMPLETED del dev (proyecto, fecha, dictamen previo,
# findings). El dev elige una. Cargar sus findings:
```
mcp__gateway__get_audit_findings({"audit_id": "<original>"})
```

## FASE 2 — Elegir qué findings retestear
```
¿Qué quieres re-verificar?
1. Todos los findings de la auditoría original
2. Solo algunos (indícame los números, ej. F-001, F-003)
```
Construir `findings_to_retest = [finding_id...]`. Por defecto, retestear los que NO estén
`FALSE_POSITIVE` (esos no aplican).

## FASE 3 — Crear el audit_run hijo
```
mcp__gateway__submit_audit({
  "asset_name": "<igual al original>",
  "asset_type": "<igual>", "audit_type": "RETEST_APROBACION", "modality": "<igual>",
  "target_url": "<igual>", "repository_url": "<igual>",
  "parent_audit_id": "<original>",
  "retest_number": <retest_number_original + 1>,
  "findings_to_retest": [<ids>],
  "skill_name": "retest-app", "plugin_version": "...", "client_os": "...", "started_at": "..."
})
```
El servidor valida que el `parent_audit_id` sea del dev. Guarda el nuevo `audit_id`.

## FASE 4 — Re-ejecutar y marcar cada finding
Si la verificación es dinámica, el usuario debe tener kali + browser arriba; si los MCP no
responden, indicarle el paso a paso (`docker compose up -d`) y detener (opencode no los levanta).
Para cada finding a retestear, **re-ejecutar el payload/PoC original** (de su `evidence`) contra
la app corregida y clasificar el resultado:

| Resultado | retest_status | Cómo se decide | Estado final del hijo |
|---|---|---|---|
| Ya no explota | `FIXED` | el payload original ya no funciona | **cerrado** (`status=FIXED`) — evidencia objetiva |
| Mitigado parcialmente | `PARTIAL` | hay un bypass del fix | queda `OPEN` → triage (FASE 5) |
| Sigue explotando | `UNFIXED` | el payload original sigue funcionando | queda `OPEN` → triage (FASE 5) |
| Estaba corregido y volvió | `REGRESSED` | regresión respecto a un retest previo | queda `OPEN` → triage (FASE 5) |

Registrar cada resultado como un finding **hijo** en el retest (con `parent_finding_id`):
```
mcp__gateway__submit_finding({
  "audit_id": "<retest_audit_id>", "title": "<igual>", "severity": "<igual>",
  "parent_finding_id": "<finding_id_original>",
  "retest_status": "FIXED | PARTIAL | UNFIXED | REGRESSED",
  "retest_notes": "<qué se observó al re-ejecutar el payload>",
  "evidence": {... request/response del retest ...},
  "dynamic_validation": { "validated": <true si sigue explotando>, ... }
})
```
> ⚠️ `submit_finding` siempre crea el hijo con `status=OPEN`. Por eso, **si `retest_status` es
> `FIXED`**, ciérralo de inmediato (la verificación dinámica es evidencia objetiva — no
> requiere triage del dev):
> ```
> mcp__gateway__update_finding_review({
>   "finding_id": "<retest_child_finding_id>", "status": "FIXED", "decision": "CONFIRMED",
>   "review_note": "Retest: el payload original ya no explota. <retest_notes>"
> })
> ```
> Los `PARTIAL`/`UNFIXED`/`REGRESSED` se dejan `OPEN` para que entren al triage de FASE 5.
Si aparecen vulnerabilidades **nuevas** (no en la original), guardarlas y pasarlas por la
consolidación (`@reference/consolidation.md`): severidad honesta (no crítico/alto sin
impacto demostrado) y fusión por mitigación, antes de registrarlas (sin `parent_finding_id`).

> Los findings de retest (hijos) son inherentemente honestos: si el payload original ya no
> explota → `retest_status: FIXED` (resuelto); si sigue explotando → `UNFIXED` con
> `dynamic_validation.validated: true` (mantiene severidad).

## FASE 5 — Cierre guiado de los UNFIXED/PARTIAL
Seguir `@reference/review-loop.md`: los `UNFIXED`/`PARTIAL` se corrigen o se justifican
(ACCEPTED_RISK con nota ≥10). Los `FIXED` ya están cerrados.

## FASE 6 — Completar (dictamen + tendencia)
```
mcp__gateway__submit_event({
  "audit_id": "<retest_audit_id>", "event_type": "AUDIT_COMPLETED",
  "findings_count": {N}, "severities": {...}, "duration_seconds": <int>
})
```
El servidor calcula el `dictamen` y la `retest_comparison`
(fixed/partial/unfixed/new + `risk_direction`: MEJORANDO/ESTABLE/EMPEORANDO).

## FASE 7 — Reporte + cierre
Lanzar `reporter` (incluye la sección **Tendencias de retest**). Al cerrar, solo informar que
el usuario puede detener kali/browser con `docker compose stop kali browser` (opencode no lo hace).

## Reglas
- Reutilizar el contexto de la auditoría original (no re-preguntar WAF/credenciales/tipo).
- `retest_status` solo en findings hijos; los nuevos van sin `parent_finding_id`.
- Eventos en MAYÚSCULA. Persistir cada resultado de inmediato.
