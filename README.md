# Agentic-Software-Governance

Repositorio que reúne **dos herramientas de auditoría para software agéntico**, pensadas
para usarse en local sobre tus propios repositorios:

| Componente | Qué es | Para qué sirve |
|---|---|---|
| **[Gobernanza por Evidencia](#gobernanza-por-evidencia-governance)** (`governance/`) | Skill de **opencode** | Revisar y documentar un repo (arquitectura, decisiones, deuda) con evidencia trazable. |
| **[Pentesting para Desarrolladores](#pentesting-para-desarrolladores-security)** (`security/`) | Agentes y skills de **opencode** (Docker) | Auditar la seguridad de tus apps: revisión de código + pruebas dinámicas OWASP. |

Ambos son **self-service y 100% locales**: no hay servidor remoto y no modifican tu
código fuente; sus salidas quedan fuera de git (ver [Datos locales](#datos-locales)).

---

## Gobernanza por Evidencia (`governance/`)

Skill de opencode (`name: gobernanza-por-evidencia`, en `governance/SKILL.md`) que
ejecuta una **revisión de gobernanza basada en evidencia** de un repositorio local.
Nunca asume: cada hallazgo cita un archivo, comando, documento o commit, con un nivel de
confianza (`alta`/`media`/`baja`). No toca el código fuente — persiste todo en una
carpeta `governance/` que genera.

**Qué hace:**

- Mapea el contexto del sistema con **arc42 reducido** (`system-context.md`).
- Audita evidencia de **código, documentación, versionado (git) y agentes/IA**.
- Registra señales especializadas (seguridad, QA, datos, performance, compliance).
- Reconstruye **decisiones de arquitectura** (ADR/MADR).
- Evalúa **deuda técnica** formal (solo en modo `profundo`).
- Genera un **reporte de gobernanza** (Markdown y, opcionalmente, PDF).

**Cómo se invoca:** desde opencode, invoca la skill `gobernanza-por-evidencia`. Antes
de escribir nada, te pedirá en un solo bloque cinco entradas:

| Entrada | Opciones |
|---|---|
| Profundidad | `normal` (señales de riesgo/deuda) · `profundo` (deuda técnica con scoring formal) |
| Audiencia | `tecnico` · `jefatura` |
| Permisos | `seguro` (solo lectura + escribir en `governance/`) · `herramientas` (además tests/lint/build/Docker) |
| Alcance | repo completo · módulo · carpeta · flujo |
| Recursos disponibles | repo local, historial git, contexto remoto, docs externas, comandos de verificación, etc. |

**Estructura interna:**

```
governance/
  SKILL.md          # punto de entrada: flujo, checklist y reglas no negociables
  scripts/          # Python: init_governance · prescan_evidence · validate_governance · render_report
  cookbooks/        # cómo recolectar evidencia (repo-search, git, docker, static-analysis, ...)
  references/       # métodos y plantillas (arc42, pyramid-*, decisions-adr-madr, technical-debt, ...)
```

> Requiere **Python 3.12** para ejecutar los scripts de apoyo (init, prescan, validate, render).

---

## Pentesting para Desarrolladores (`security/`)

Conjunto de agentes y skills de [opencode](https://opencode.ai) que audita la seguridad de **tus propias
aplicaciones** desde tu máquina, combinando **revisión de código** (Caja Blanca) y
**pruebas dinámicas OWASP** (Web, API, chatbots/LLM y workflows/nodos de n8n). Te explica
cada vulnerabilidad en lenguaje simple y te ayuda a corregirla.

Corre **100% local con Docker** (contenedores `kali`, `browser`, `gateway`, `mongodb`
conectados como MCP). No hay servidor remoto ni autenticación; tus auditorías se guardan
en una MongoDB local.

> ⚠️ **Solo en entornos locales o de prueba.** Ejecuta ataques reales que pueden crear,
> editar y eliminar datos. Nunca lo uses contra producción.

📖 **Documentación completa (requisitos, puesta en marcha, MCP, comandos): [`security/README.md`](security/README.md).**

---

## Estructura del repositorio

```
.
├── README.md         # este archivo (portada)
├── .gitignore
├── governance/       # skill de opencode: gobernanza por evidencia
└── security/         # agentes y skills de opencode: pentesting local (ver su propio README)
```

---

## Requisitos

- **Gobernanza:** [opencode](https://opencode.ai) + **Python 3.12** (scripts de apoyo).
- **Pentesting:** **Docker** + **Docker Compose** y **opencode** — detalle en [`security/README.md`](security/README.md).

---

## Datos locales

Las salidas de ambas herramientas son **locales** y quedan **fuera de git** (`.gitignore`):

- La carpeta `governance/` generada por una revisión (evidencia, decisiones, reportes).
- `security/audits/` — evidencia, findings y reportes de cada auditoría.

El historial de pentesting vive además en la MongoDB local del contenedor `pentesting-mongodb`.
