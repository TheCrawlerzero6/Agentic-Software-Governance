---
name: mis-auditorias
description: Consulta tus auditorías pasadas, revisa findings pendientes (corregir / justificar), regenera reportes, prioriza hallazgos o pide explicación de una vulnerabilidad. Todo local.
---

# mis-auditorias

> La orquestación de este flujo la lleva el **agente primary `pentest`**
> (`.opencode/agent/pentest.md`), que es la fuente de verdad. Úsalo con el comando
> `/mis-auditorias` o seleccionándolo con Tab.

Si llegas aquí por la tool `skill`, comportarte como el **Flujo B (Mis auditorías)** del agente
`pentest`: verificar el gateway local, listar las auditorías (`get_audits`) y entrar al hub (ver
findings, revisar pendientes con `reference/review-loop.md`, marcar un finding suelto con
`reference/review-finding.md`, regenerar reporte, triage, explicar vulnerabilidad, o retest con
`reference/retest-app.md`). Nombres de estado amigables según `reference/review-loop.md`.
