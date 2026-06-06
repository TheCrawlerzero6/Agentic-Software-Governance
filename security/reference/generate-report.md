# Skill: Generar Reporte

## Cuando activar

El desarrollador menciona: "genera el reporte", "quiero el informe", "dame el reporte",
"report", "resumen de la auditoría", "necesito el documento".

## Flujo

### PASO 1 — Identificar auditoría

Si la auditoría acaba de terminar en la misma sesión: usar la actual.

Si no hay contexto, buscar localmente:
```bash
ls -d audits/*/findings.json 2>/dev/null
```

O consultar gateway:
```
mcp__gateway__get_audits()
```

Si hay múltiples:
```
Encontré estas auditorías:
1. mi-api (2026-03-21) — 4 vulnerabilidades
2. mi-frontend (2026-03-20) — 2 vulnerabilidades

¿Cuál quieres reportar?
```

### PASO 2 — Seleccionar formato

```
¿Cómo quieres el reporte?

1. Markdown (recomendado) — archivo report.md en tu proyecto, opencode puede
   leerlo y corregir las vulnerabilidades automáticamente
2. Resumen en chat — lo muestro aquí directamente
```

### PASO 3 — Generar

Antes de generar, advertir si quedan findings sin cerrar (status OPEN o
`analyst_review.decision == PENDING`): el reporte los marcará como abiertos. Preguntar si
generar igual.

Lanzar el reporter agent. Genera `security-report.md` con dictamen + métricas de calidad +
badges explotable/no-explotable (+ tendencias si es retest), la cabecera
`<!-- PENTEST_VERIFY -->` y el `report_sha256` para el gate de CI:
```
Agent(subagent_type="pentesting-para-desarrolladores:reporter",
      prompt="[audit_id={audit_id}] Genera security-report.md (modelo rico: dictamen,
              métricas, badges, código corregido). Incluye la cabecera PENTEST_VERIFY,
              calcula report_sha256 y emite REPORT_GENERATED.")
```

### PASO 4 — Post-reporte

```
📊 Reporte generado: security-report.md

¿Qué quieres hacer?
1. Que corrija las vulnerabilidades automáticamente
2. Explicarme una vulnerabilidad en detalle
3. Nada por ahora
```

Si elige 1: leer report.md, aplicar cada `fix_suggestion` con la herramienta Edit.
Si elige 2: activar skill explain-finding.
