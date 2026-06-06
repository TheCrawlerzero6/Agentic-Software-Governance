# Flow interno: Code review de nodo custom de n8n

Audita el **código fuente** (TypeScript/JavaScript) de un nodo custom de n8n
(`asset_type = node_n8n`). Es distinto de `n8n-audit.md`, que analiza el JSON de un
workflow. Aquí se hace code review del nodo en sí (su `.node.ts`, `.credentials.ts`,
`package.json`, helpers). La lógica vive en el agente `pentester-n8n` (modo nodo).

## Cuándo activar
El dev menciona: "nodo custom de n8n", "mi nodo de n8n", "revisa el código de mi nodo n8n",
"n8n-nodes-...". También desde `pentest-app.md` cuando el activo es `node_n8n`.

## FASE 1 — Intake mínimo
Preguntar (UNA a la vez) si el intake no lo capturó:
```
1. Ruta del código del nodo (carpeta o .zip con el package)
2. Nombre del nodo / paquete (ej: n8n-nodes-mi-integracion)
```

## FASE 2 — Registrar la auditoría
```
mcp__gateway__submit_audit({
  "asset_name": "<nombre del nodo>", "asset_type": "node_n8n",
  "audit_type": "APROBACION_ACTIVOS", "modality": "WHITE_BOX",
  "target_url": "host.docker.internal",   // estático; el nodo no es un servicio
  "source_code_path": "<ruta>", "language": "typescript", "repository_url": "<repo>",
  "skill_name": "n8n-node-review", "plugin_version": "...", "client_os": "...", "started_at": "..."
})
```
> El nodo no es un servicio con URL; usar `host.docker.internal` como `target_url` para
> pasar la validación de scope (es análisis estático, no se prueba una URL).

## FASE 3 — Code review (delegado al agente)
```
Agent(subagent_type="pentesting-para-desarrolladores:pentester-n8n",
      prompt="[audit_id={audit_id}] [target=node_n8n: ruta={ruta}] Modo NODO: code review
              del código TS/JS del nodo custom. Registra findings con sec/check_id.")
```
El agente revisa (ver detalle en `agents/pentester-n8n.md`):
- `n8n_node_inj` — inyección (command/SQL/eval) sobre parámetros del nodo o items.
- `n8n_node_cred` — manejo inseguro de credenciales (logs, reenvío, claro).
- `n8n_node_input` — falta de validación de `getNodeParameter()` / items entrantes.
- `n8n_node_ssrf` — requests a URLs construidas con input sin validar.
- `n8n_node_deps` — dependencias vulnerables en el package.json del nodo.
- `n8n_node_secret` — secretos hardcodeados en el código.

Cada finding lleva `evidence.vulnerable_code` + `fix_suggestion` (TS/JS) y `evidence.node_name`.
El agente los guarda en `audits/{dir}/findings_n8n.json` (no los registra aún).

## FASE 3.5 — Consolidación (gating + fusión + registro)
Seguir `@reference/consolidation.md`: gatear severidad por impacto real (code review
estático → potencial salvo versión con CVE+PoC), fusionar por mitigación (deps vulnerables
con el mismo `npm update` → 1 finding) y registrar con `submit_finding`.

## FASE 4 — Cierre guiado
Seguir `@reference/review-loop.md` con el `audit_id`. El "fix" es Edit en el código del
nodo (igual que un code review normal).

## FASE 5 — Completar + reporte + cierre
Emitir `AUDIT_COMPLETED` (dictamen server-side), lanzar `reporter`. Es análisis estático: no
requiere contenedores. opencode no levanta ni detiene nada.

## Reglas
- Análisis estático: leer el código, NO ejecutar el nodo.
- Corrección accionable dentro del código del nodo.
- Eventos en MAYÚSCULA. Persistir findings de inmediato.
