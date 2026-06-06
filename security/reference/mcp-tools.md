# Herramientas MCP — Plugin para Desarrolladores

Catálogo de herramientas disponibles con clasificación Tier 1/Tier 2.

## Regla general

- Herramientas Kali SIEMPRE via MCP (`mcp__kali__*`), NUNCA via Bash `docker exec`
- Requests HTTP via `mcp__kali__execute_command` (curl), NUNCA via Bash directo
- Browser SIEMPRE via MCP (`mcp__browser__*`)
- Si los MCPs no responden: detener y avisar al dev

## Tier 1 — Auto-aprobado

Herramientas de descubrimiento y escaneo pasivo/semi-pasivo que se pueden ejecutar
sin pedir permiso al dev:

| Herramienta | Propósito | Comando MCP |
|-------------|-----------|-------------|
| nmap | Puertos y servicios | `mcp__kali__nmap_scan` |
| gobuster | Directorios y endpoints ocultos | `mcp__kali__gobuster_scan` |
| nuclei | Fingerprinting y detección de vulns conocidas | `mcp__kali__execute_command("nuclei -u {url} -as -silent")` |
| arjun | Descubrimiento de parámetros HTTP | `mcp__kali__execute_command("arjun -u {url} -t 30")` |
| dalfox | Detección de XSS | `mcp__kali__execute_command("dalfox url '{url}' --timeout 30")` |
| corsy | Detección de CORS misconfiguraciones | `mcp__kali__execute_command("corsy -u {url}")` |
| crlfuzz | Detección de CRLF injection | `mcp__kali__execute_command("crlfuzz -u {url}")` |
| jwt_tool | Análisis de tokens JWT | `mcp__kali__execute_command("python3 /opt/jwt_tool/jwt_tool.py {token}")` |
| curl | Requests HTTP manuales | `mcp__kali__execute_command("curl --connect-timeout 10 --max-time 30 ...")` |
| browser_navigate | Navegar a una URL | `mcp__browser__browser_navigate` |
| browser_screenshot | Capturar estado visual | `mcp__browser__browser_screenshot` |
| browser_fill | Llenar formularios | `mcp__browser__browser_fill` |
| browser_click | Hacer clic en elementos | `mcp__browser__browser_click` |
| browser_eval_js | Ejecutar JavaScript | `mcp__browser__browser_eval_js` |
| proxy_start | Iniciar proxy para interceptar tráfico | `mcp__browser__proxy_start` |
| proxy_get_flows | Ver flujos interceptados | `mcp__browser__proxy_get_flows` |

## Tier 2 — Requiere aprobación del dev

Herramientas que ejecutan ataques activos. SIEMPRE mostrar el diálogo de aprobación
y esperar respuesta del dev ANTES de ejecutar:

| Herramienta | Por qué requiere aprobación | Comando MCP |
|-------------|---------------------------|-------------|
| sqlmap | Puede modificar o corromper datos en la DB | `mcp__kali__sqlmap_scan` |
| hydra | Fuerza bruta — puede bloquear cuentas | `mcp__kali__hydra_attack` |
| metasploit | Explotación activa — puede afectar el funcionamiento de la app | `mcp__kali__metasploit_run` |

### Diálogo de aprobación Tier 2

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIER 2 — Requiere tu aprobación
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Check: {nombre del check}
Herramienta: {tool}
Por qué: {riesgo en lenguaje simple para el dev}
Target: {endpoint o parámetro específico}

¿Autorizas? (sí/no)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Si el dev dice "no": omitir el check, documentar como "omitido por decisión del dev".
Si el dev dice "sí": ejecutar la herramienta.

## Tool Announcement

Antes de CADA tool call de seguridad, anunciar con `🔧`:

```
🔧 nmap -sV → {target} — Escaneando puertos y servicios
🔧 nuclei -u {target} -as — Fingerprinting y detección de tecnologías
🔧 gobuster dir -u {target} — Buscando directorios y endpoints ocultos
🔧 dalfox url '{url}' — Detectando XSS en parámetros
🔧 corsy -u {target} — Detectando CORS misconfiguraciones
🔧 curl {url} — {descripción del check}
🔧 sqlmap --url {url} — SQL injection (Tier 2 — aprobado por dev)
```

## Tiempos de ejecución

### Herramientas rápidas — timeout estático obligatorio

| Herramienta | Flag de timeout |
|-------------|----------------|
| `curl` | `--connect-timeout 10 --max-time 30` |
| `arjun` | `-t 30` |
| `dalfox` | `--timeout 30` |

### Herramientas lentas — NO matar con timeout estático

| Herramienta | Tiempo típico | Flags recomendadas |
|-------------|---------------|---------------------|
| `nuclei` | 2-10 min | `-as -silent` |
| `nmap` | 1-5 min | `-sV --host-timeout 60s` |
| `sqlmap` | 2-8 min | `--batch --level=2 --risk=2` |
| `gobuster` | 1-5 min | wordlist estándar |

Si tarda >5 minutos: verificar `docker inspect --format '{{.State.Health.Status}}' pentesting-kali`.
Solo cancelar si container caído o error explícito. NUNCA cancelar solo por tiempo.

## Herramientas PROHIBIDAS

- `nikto` — NUNCA usar. Demasiado lento y sin resultados útiles.

## Si los MCPs no responden

NO usar Bash como alternativa. NO intentar `docker exec pentesting-kali`.
Detener y avisar al dev que verifique los containers y reinicie opencode.

Bash está reservado EXCLUSIVAMENTE para: leer archivos del proyecto, detectar
containers del desarrollador (`docker ps`, `docker inspect`), y detectar frameworks.

## Tools del equipo de seguridad Gateway (registro de datos)

Para registrar auditorías, hallazgos, eventos y sesiones LLM se usan las tools del
`gateway` (NO se inserta directo en MongoDB):

| Tool | Para qué |
|---|---|
| `mcp__gateway__submit_audit` | Crear el audit_run al iniciar |
| `mcp__gateway__submit_finding` | Registrar un hallazgo (modelo rico) |
| `mcp__gateway__update_finding_review` | Clasificar/cerrar un finding (status + nota) |
| `mcp__gateway__update_finding_triage` | Priorización (CVSS/explotabilidad) |
| `mcp__gateway__submit_event` | Telemetría y ciclo de vida |
| `mcp__gateway__submit_llm_session` | Sesión de ataque al chatbot |
| `mcp__gateway__get_audits` / `get_audit_findings` | Consultar |

> **El gateway valida cada documento con `$jsonSchema`** y rechaza datos malformados. Cómo
> construir los argumentos (enums en MAYÚSCULA, campos obligatorios, mapeo intake→args y el
> manejo de `schema_validation_failed`): **`@reference/gateway-persistence.md`**.
