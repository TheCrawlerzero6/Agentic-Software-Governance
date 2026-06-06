# Skill: Priorizar Vulnerabilidades

## Cuando activar

El desarrollador menciona: "priorizar", "triage", "qué es más crítico",
"qué arreglo primero", "cuál es más importante", "ordenar por prioridad".

## Flujo

### PASO 1 — Identificar auditoría

Si hay auditoría reciente en la sesión: usar esa.
Si no: buscar localmente o en gateway.

### PASO 2 — Ejecutar triage

Lanzar agente triage:
```
Agent(subagent_type="pentesting-para-desarrolladores:triage",
      prompt="Prioriza los findings de audit_id={audit_id}")
```

> **CVSS riguroso (opcional):** si los findings no traen `cvss_score`/`cvss_vector` o quieres
> recalcularlos según FIRST.org, lanzar antes el agente `cvss-scorer`
> (`Agent(subagent_type="pentesting-para-desarrolladores:cvss-scorer", prompt="[audit_id=...]")`).
> El triage usa `dynamic_validation` como factor principal; el cvss-scorer fija el CVSS base.

### PASO 3 — Presentar en lenguaje dev

```
📊 Priorización de vulnerabilidades
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 CORREGIR AHORA:
1. Inyección NoSQL en login (src/controllers/auth.js:45) — un atacante puede acceder sin credenciales
2. IDOR en perfil de usuario (src/routes/users.js:23) — cualquier usuario ve datos de otros

🟡 CORREGIR PRONTO:
3. CORS sin restricción (src/app.js:12) — otros sitios pueden hacer requests a tu API
4. Headers de seguridad faltantes — la app no indica al navegador cómo protegerse

🟢 CUANDO PUEDAS:
5. Versión del servidor expuesta — un atacante sabe qué tecnología usas

¿Quieres que corrija las vulnerabilidades empezando por las más críticas?
```

## Reglas

- Lenguaje developer-friendly en las descripciones
- Explicar el IMPACTO real, no solo la categoría técnica
- Ofrecer corrección automática al final
