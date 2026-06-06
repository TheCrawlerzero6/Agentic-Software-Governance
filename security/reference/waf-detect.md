# Skill: Detectar WAF

## Cuando activar

El desarrollador menciona: "WAF", "firewall", "está protegido", "tiene protección",
"cloudflare", "antes de auditar quiero saber si tiene WAF".

## Flujo

### PASO 1 — Obtener URL

Si no la dio:
```
Dame la URL del target para detectar si tiene WAF:
```

### PASO 2 — Ejecución (delegada al agente)

```
Agent(subagent_type="pentesting-para-desarrolladores:waf-detect",
      prompt="[target={url}] [audit_id={si aplica}] Detecta WAF/protecciones con las 5 probes Tier 1.")
```
El agente `waf-detect` corre: nuclei WAF fingerprint, análisis de headers, y probes SQLi /
path traversal / XSS comparando contra una request benigna (ver `agents/waf-detect.md`).

### PASO 3 — Resultado

```
Resultado: {WAF detectado / No se detectó WAF}

{Si detectado:}
WAF: {nombre} ({proveedor})
Comportamiento: {qué bloquea}

Si tu app está en Docker local, normalmente no tiene WAF.
Si lo tiene, es probable que sea un reverse proxy configurado en tu docker-compose.
```

## Reglas

- Es Tier 1 (automático, sin pedir permiso)
- Solo 5 requests — rápido y no intrusivo
