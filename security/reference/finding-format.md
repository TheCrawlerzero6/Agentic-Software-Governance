# Formato de Hallazgos — Plugin para Desarrolladores

> La **fuente de verdad del documento de finding** es `reference/schema/finding.md`
> (modelo rico, enums MAYUSCULA, igual que el modelo de referencia). Este archivo solo cubre
> la estructura de archivos locales, las reglas de IDs y la consolidacion por causa raiz.

## Estructura de directorios de auditoría

```
./audits/{timestamp}_{target}/
├── findings.json          ← hallazgos locales (respaldo del modelo de schema/finding.md)
├── findings_pending.json  ← cola de hallazgos pendientes de sync con el gateway
├── directives.json        ← directivas del code review para el pentesting dinámico
├── triage_results.json    ← resultados del triage de priorización
├── evidence/              ← evidencia adicional (requests, responses, screenshots)
│   └── llm/               ← evidencia de chatbot (solo si el activo es un bot)
├── security-report.md     ← reporte final (el dev lo sube a pentesting/ en su repo)
└── summary.md             ← resumen breve de la auditoría
```

## Formato del hallazgo

Ver **`reference/schema/finding.md`**. Todo finding (local y en el gateway) DEBE
satisfacer esa interfaz. Puntos clave que cambian respecto a la version anterior:

- `severity` y `status` van en **MAYUSCULA** (`CRITICAL`, `OPEN`, `FIXED`, ...).
- El estado de cierre vive en `status` + `analyst_review.decision` (no en `review_status`).
- `dynamic_validation.validated` marca si el hallazgo es **EXPLOTABLE** (true) o no (false).
- Campos por tipo: code-review (`source_file`, `cwe_id`, `evidence.vulnerable_code`,
  `evidence.fix_suggestion`); chatbot (`evidence.llm_check_id`, `evidence.conversation_log[]`);
  n8n (`evidence.sec_id`, `evidence.node_name`).

## IDs de hallazgos

- `finding_id` (unico global en el gateway): `plugin_{target-slug}_F{NNN}`
  (ej. `plugin_mi-api_F001`). Nunca solo `F-001` — causa colision.
- `display_id` (visual en el reporte): `F-001`, `F-002`... consecutivos sin saltos.
  Si se eliminan hallazgos durante la revision → renumerar el `display_id`.

## Orden de hallazgos en el reporte

Siempre por severidad descendente: **CRITICAL > HIGH > MEDIUM > LOW > INFO**.
Luego por `cvss_score` descendente. `F-001` = el mas critico. Nunca en orden de descubrimiento.

## Consolidación / fusión por mitigación (AUTOMÁTICA)

Los hallazgos que comparten la **misma mitigación** (mismo fix / misma `root_cause`) se
**fusionan automáticamente** en uno solo durante la fase de consolidación
(`@reference/consolidation.md`), listando todos los recursos/endpoints afectados, para que
el dev arregle una sola vez. Ejemplos: 5 endpoints con SQLi por la misma función `buildQuery()`
→ 1 finding con los 5; 3 endpoints sin rate limiting → 1 finding; 4 deps EOL que se arreglan
con el mismo `npm update` → 1 finding. La severidad del fusionado = la más alta del grupo
(ya gateada por impacto real). NO se pierde trazabilidad: cada recurso queda en la evidencia.

## Severidad honesta

La severidad refleja **impacto demostrado** (explotación confirmada, o versión con CVE+PoC
público). Lo no explotable/no verificado se degrada a MEDIO máximo. Ver la política en
`@reference/rules.md` y el algoritmo en `@reference/consolidation.md`.

## Niveles de confianza (`confidence`)

| Confidence | Cuándo usar |
|---|---|
| `confirmed` | Se reprodujo el PoC y se verificó el efecto real (`dynamic_validation.validated = true`) |
| `high` | Evidencia fuerte pero sin PoC completo |
| `medium` | Indicios claros en el código o la respuesta HTTP |
| `low` | Análisis estático, sin validación dinámica |
| `suspected` | Posible vulnerabilidad, evidencia insuficiente |

**HTTP 200 NO es confirmación.** Si no se puede confirmar el efecto real → `suspected`,
`dynamic_validation.validated = false`, y bajar la severidad un nivel.
