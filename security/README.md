# Pentesting para Desarrolladores — versión opencode (100% local)

Agentes y skills de pentesting **self-service** para [opencode](https://opencode.ai): audita la seguridad
de tus propias aplicaciones desde tu máquina, combinando **revisión de código** (Caja Blanca) y
**pruebas dinámicas** OWASP (Web, API, chatbots/LLM y workflows/nodos de n8n). Te explica cada
vulnerabilidad en lenguaje simple, con un ejemplo de cómo la aprovecharía un atacante, y te ayuda
a corregirla.

Todo corre en **local con Docker**: clonas el repo, levantas los contenedores y empiezas. **No hay
servidor remoto ni autenticación** — tus auditorías y hallazgos se guardan en una MongoDB local.

> ⚠️ **Solo en entornos locales o de prueba.** Estos agentes ejecutan ataques reales que pueden crear,
> editar y eliminar datos. Nunca lo uses contra producción. Ten un backup de tu base de datos.

---

## Cómo funciona

```
opencode  (lee opencode.json → conecta 3 MCP)
   ├── kali     → herramientas de pentesting (nmap, sqlmap, nuclei, dalfox, jwt_tool, ...)
   ├── browser  → automatización de navegador (Playwright/Chromium) para apps web
   └── gateway  → guarda auditorías/findings/eventos en MongoDB (sin autenticación)

docker compose (en este repo) levanta:
   pentesting-kali (5000) · pentesting-browser (3478) · pentesting-gateway (3480) · pentesting-mongodb
```

- **Agente orquestador** (`.opencode/agent/pentest.md`, `mode: primary`): el punto de entrada que
  guía toda la auditoría y delega en los subagentes. Selecciónalo con Tab o úsalo con los comandos.
- **Comandos** (`.opencode/command/`): atajos `/pentesting` (auditar / retest / CVE) y
  `/mis-auditorias` (revisar hallazgos, triage, reportes) — ambos corren bajo el agente `pentest`.
- **Subagentes** (`.opencode/agent/`): 13 especialistas que el orquestador invoca (intake,
  code-reviewer, pentester-web/api/chatbot/n8n/coder, cvss-scorer, exploit-research, triage,
  waf-detect, reporter, supervisor).
- **Skills** (`.opencode/skills/`): `pentesting` y `mis-auditorias` — stubs que apuntan al agente
  `pentest` (la lógica vive en el agente y en `reference/`).
- **Referencias** (`reference/`): flujos detallados, esquemas de datos y corpus de ataques que leen
  el agente y los subagentes.

---

## Requisitos

- **Docker** y **Docker Compose** (Docker Desktop en Windows/macOS).
- **opencode** instalado ([guía](https://opencode.ai/docs/)).
- ~6 GB de disco para las imágenes (la de Kali es la más grande).

---

## Puesta en marcha

```bash
# 1. Clonar
git clone <URL_DE_ESTE_REPO> pentesting-open-code
cd pentesting-open-code

# 2. (Opcional) configurar variables locales
cp .env.example .env        # en Windows: copy .env.example .env

# 3. Levantar el entorno (la primera vez compila kali/browser; tarda unos minutos)
docker compose up -d
docker compose ps           # espera a que estén "healthy"

# 4. Abrir opencode en esta carpeta
opencode
```

> **Importante:** el ciclo de vida de los contenedores lo manejas **tú**. opencode no ejecuta
> `docker compose`: solo verifica que los MCP estén disponibles y, si no, te muestra el paso a
> paso. Levanta el entorno (`docker compose up -d`) **antes** de abrir opencode; si lo levantas
> después, reinicia opencode para que cargue los MCP de `opencode.json`.

En opencode, lanza una auditoría:

```
/pentesting
```

o simplemente describe lo que quieres ("audita mi API en localhost:3000"). El agente de intake
te guiará paso a paso (detecta tu app en Docker, te pide el código y las credenciales por rol).

Para revisar resultados pasados:

```
/mis-auditorias
```

---

## Configuración (`opencode.json`)

Los 3 MCP ya están declarados:

| MCP | Tipo | Destino |
|---|---|---|
| `kali` | local (stdio) | `docker exec` al contenedor `pentesting-kali` |
| `browser` | remote | `http://localhost:3478/sse` |
| `gateway` | remote | `http://localhost:3480/mcp` |

`opencode.json` también inyecta las referencias universales (`reference/rules.md`,
`mcp-tools.md`, `finding-format.md`) en el contexto y deja `edit`/`bash` en modo aprobación.

### Variables (`.env`)

| Variable | Por defecto | Para qué |
|---|---|---|
| `AUDIT_OWNER` | `local` | Identidad/owner con el que se guardan las auditorías. |
| `ALLOWED_TARGET_DOMAINS` | *(vacío)* | Dominios extra permitidos como objetivo (coma). Por defecto solo `localhost` + redes privadas (RFC1918). |
| `TZ_OFFSET_HOURS` | `0` | Desfase horario de los timestamps (0 = UTC). |

---

## Dónde quedan tus datos

Todo se guarda **local** en la MongoDB del contenedor (`pentesting_mongodb`, base `pentest_audits`):

- `audit_runs` — auditorías (estado, dictamen, retest).
- `findings` — hallazgos (severidad, CVSS, validación dinámica, triage, estado).
- `events` — telemetría local de la auditoría.
- `llm_attack_sessions` — sesiones de ataque a chatbots/LLM.

Los validadores `$jsonSchema` se aplican al inicializar la base
(`containers/gateway/init-mongo-schema.js`). La evidencia y los reportes Markdown se generan en
`audits/` (ignorada por git). El reporte final (`security-report.md`) lo puedes copiar a una
carpeta `pentesting/` en tu propio repo.

Consultar la base directamente:

```bash
docker exec pentesting-mongodb mongosh pentest_audits --quiet --eval "db.findings.find().limit(3)"
```

---

## Parar / limpiar

```bash
docker compose stop kali browser   # liberar recursos (conserva tu historial)
docker compose down                # parar todo (conserva el volumen de Mongo)
docker compose down -v             # parar y BORRAR la base de datos (¡pierdes el historial!)
```

---

## Solución de problemas

- **opencode no ve los MCP** → asegúrate de que los contenedores estén `healthy`
  (`docker compose ps`) y reinicia opencode para que recargue `opencode.json`.
- **`gateway no responde`** → `docker compose logs gateway` y verifica que `mongodb` esté healthy.
- **El target es rechazado (`target_out_of_scope`)** → solo se permiten `localhost`/redes privadas;
  añade tu host interno a `ALLOWED_TARGET_DOMAINS` en `.env` y reinicia el gateway.
- **La imagen de Kali tarda** → es normal la primera vez (`docker compose build kali` para verlo).

---

## Estructura del repo

```
opencode.json            # MCP + permisos + instrucciones
docker-compose.yml       # kali + browser + gateway + mongodb
.env.example
.opencode/
  agent/                 # pentest (primary) + 13 subagentes
  skills/                # pentesting, mis-auditorias (stubs → agente pentest)
  command/               # /pentesting, /mis-auditorias (agent: pentest)
reference/               # flujos, schema/, corpus/
scripts/                 # ayudas opcionales que ejecutas TÚ (ensure/stop-containers); opencode no las llama
containers/
  kali/  browser/  gateway/
```
