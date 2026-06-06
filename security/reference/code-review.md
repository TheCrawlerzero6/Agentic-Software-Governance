# Skill: Revisar Código

## Cuando activar

El desarrollador menciona: "revisa mi código", "code review", "analiza el código",
"busca vulnerabilidades en el código", "revisa la seguridad del código fuente".

## Flujo

### PASO 1 — Detectar código

Intentar auto-detectar en el directorio de trabajo actual:
```bash
ls package.json requirements.txt go.mod pom.xml Gemfile composer.json 2>/dev/null
```

Si encuentra: confirmar con el dev.
```
Detecté un proyecto {lenguaje}/{framework} en el directorio actual.
¿Es este el código que quieres que revise? (sí/no)
```

Si no encuentra: pedir la(s) carpeta(s).
```
¿Cuál es la ruta del código que quieres que revise?
- Si está todo en una carpeta, pásame esa (ej: ./src, ../mi-app).
- Si está separado (frontend, backend, otra), pásame la ruta de cada parte.
```
Verificar cada ruta con `ls`. Guardar `roots = [{role, path}]` (igual que el intake).

### PASO 2 — Registrar la auditoría
```
mcp__gateway__submit_audit({
  "asset_name": "{nombre del proyecto}", "asset_type": "{api|web|web_api}",
  "audit_type": "APROBACION_ACTIVOS", "modality": "WHITE_BOX",
  "target_url": "host.docker.internal",   // code review estático, sin app corriendo
  "source_code_path": "{ruta}", "language": "{lang}", "framework": "{fw}",
  "repository_url": "{repo}", "skill_name": "code-review",
  "plugin_version": "...", "client_os": "...", "started_at": "..."
})
```

### PASO 3 — Code review (delegado al agente)
```
Agent(subagent_type="pentesting-para-desarrolladores:code-reviewer",
      prompt="[audit_id={audit_id}] [source_code_path={raíz principal}]
              [source_code_paths={todas las raíces, coma-separadas}] [language] [framework]
              Analiza el código de TODAS las raíces y registra findings (modelo rico). Genera directives.json.")
```
El agente busca inyección, secrets, IDOR, SSRF, auth, crypto y deps vulnerables por
lenguaje, y registra cada finding con `source_file`, `vulnerable_code` y `fix_suggestion`
(ver `agents/code-reviewer.md`). Presentar el resumen dev-friendly que devuelve.

### PASO 5 — Cierre guiado de findings (obligatorio si hay findings)

**Si hay 0 findings:** saltar al PASO 6.

**Si hay findings:** entrar automáticamente al loop guiado siguiendo las
instrucciones de `@reference/review-loop.md` con el `audit_id` actual.

El loop:
1. **FASE 1 — Triage:** clasificar cada finding como Confirmada / Falso
   positivo / Aceptación de riesgo / Fuera de alcance.
2. **FASE 2 — Fix:** sobre cada Confirmada, aplicar corrección.

Cuando retorne, mostrar el menú post-revisión:

### PASO 6 — Menú post-revisión

```
¿Algo más?

1. Generar reporte Markdown
2. Continuar con pentesting dinámico (probar contra la app corriendo)
3. Terminar
```

Si el dev elige "Generar reporte" con findings pendientes, advertir igual que
en `pentest-app.md` FASE 7.

## Reglas

- SIEMPRE incluir archivo:línea exacta
- SIEMPRE incluir código vulnerable + código corregido
- No usar terminología OWASP en los títulos — descripciones claras
- Priorizar por impacto real (inyección SQL > header faltante)
