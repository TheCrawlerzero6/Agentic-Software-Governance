# Gobernanza por Evidencia

Guia de uso para ejecutar una revision de gobernanza tecnica sobre un repositorio local. La revision crea una carpeta `governance/` dentro del proyecto revisado y guarda ahi contexto del sistema, evidencia, decisiones, deuda tecnica, acciones recomendadas y reportes.

Esta skill esta pensada para revisar proyectos propios o autorizados. No usa servidor remoto, no guarda datos fuera del proyecto y no instala herramientas. Todo queda como Markdown y archivos generados dentro de `governance/`.

---

## Para que sirve

Usala cuando quieras responder, con evidencia escrita:

- que hace el sistema;
- cuales son sus flujos principales;
- que arquitectura o estructura se puede inferir;
- que documentacion existe o falta;
- que decisiones tecnicas estan documentadas, inferidas o ausentes;
- que senales potenciales requieren revision especializada;
- que deuda tecnica existe, si se usa modo profundo;
- que acciones conviene corregir, posponer, descartar o derivar;
- que reporte final entregar a un perfil tecnico o de jefatura.

No es una herramienta de pentesting ni de QA especializada. Puede registrar senales potenciales de seguridad, QA, datos, performance o compliance, pero no confirma vulnerabilidades, amenazas, fallos QA o incumplimientos sin evidencia directa.

---

## Requisitos

- Python 3 disponible como `python3`.
- Acceso local al repositorio que quieres revisar.
- Un cliente de IA que pueda leer la carpeta de la skill o recibir sus instrucciones.
- Opcional: git, Docker, tests, linters, GitHub CLI, MCPs o reportes existentes. Si no existen, la revision puede continuar con evidencia local.

No necesitas base de datos, servidor remoto ni autenticacion.

---

## Estructura de la skill

```text
gobernanza-por-evidencia/
  SKILL.md
  readme.md
  scripts/
    init_governance.py
    prescan_evidence.py
    validate_governance.py
    render_report.py
  references/
  cookbooks/
```

`SKILL.md` contiene el flujo operativo para el agente. Este `readme.md` explica como usar la skill y que esperar de ella.

---

## Modos de revision

| Opcion | Valores | Efecto |
|---|---|---|
| Profundidad | `normal` | Contexto, evidencia, decisiones, senales potenciales e insights. No hace evaluacion formal de deuda. |
| Profundidad | `profundo` | Incluye deuda tecnica formal con prioridad, evidencia, costo, interes y decision de gestion. |
| Audiencia | `tecnico` | El reporte usa mas detalle de arquitectura, rutas, comandos, modulos y evidencia tecnica. |
| Audiencia | `jefatura` | El reporte prioriza resumen ejecutivo, decisiones, impacto, confianza y proximas acciones. |
| Permisos | `seguro` | Solo lectura local, busqueda, git local de solo lectura y escritura en `governance/`. |
| Permisos | `herramientas` | Permite ejecutar tests, lint, build, Docker o comandos del proyecto si estan autorizados. |

La audiencia solo cambia la forma del reporte. No cambia la evidencia revisada ni las conclusiones.

---

## Puesta en marcha rapida

Desde la raiz del proyecto que quieres revisar:

```bash
python3 gobernanza-por-evidencia/scripts/init_governance.py \
  --root . \
  --depth normal \
  --audience tecnico \
  --permissions seguro \
  --scope "repo completo" \
  --quiet
```

Luego ejecuta el pre-scan:

```bash
python3 gobernanza-por-evidencia/scripts/prescan_evidence.py --root . --quiet
```

Cuando la revision este completa, valida:

```bash
python3 gobernanza-por-evidencia/scripts/validate_governance.py --root . --strict --quiet
```

Si se elige generar PDF:

```bash
python3 gobernanza-por-evidencia/scripts/render_report.py --root . --quiet
```

---

## Flujo completo

1. **Configurar revision**
   - Define profundidad, audiencia, permisos, alcance y recursos disponibles.
   - Se registra en `governance/governance-config.md`.

2. **Explorar base del proyecto**
   - Se ejecuta un pre-scan no destructivo.
   - Se detectan manifests, lockfiles, documentacion, tests, Docker, git y reglas de agentes.

3. **Entender sistema y flujos**
   - Se completa `governance/system-context.md`.
   - Usa una version reducida de arc42: proposito, restricciones, bloques, flujos, despliegue, decisiones y limitaciones.

4. **Revisar evidencia por capas**
   - Codigo: `governance/evidence/code.md`.
   - Documentacion: `governance/evidence/documentation.md`.
   - Versionado: `governance/evidence/versioning.md`.
   - Reglas de agentes: `governance/evidence/agents.md`.

5. **Registrar evidencias potenciales**
   - Seguridad, QA, datos, performance y compliance se registran en `governance/evidence/specialized/`.
   - Estas entradas son potenciales por defecto.

6. **Reconstruir decisiones**
   - Se completa `governance/decisions.md`.
   - Se separan decisiones documentadas, inferidas, faltantes y contradictorias.

7. **Evaluar deuda tecnica**
   - Solo en modo `profundo`.
   - Se registra en `governance/technical-debt.md`.
   - Cada deuda debe tener artefacto, escenario de cambio, constructo que encarece el cambio, evidencia y decision de gestion.

8. **Registrar insights accionables**
   - Se completa `governance/action-register.md`.
   - Cada insight queda listo para decidir: corregir seguro, posponer, descartar o derivar.

9. **Validar base de gobernanza**
   - Se ejecuta `validate_governance.py --strict`.
   - Si falla, se corrigen los archivos de `governance/` hasta que pase.

10. **Seleccionar y resolver insights**
   - Se decide que hacer con cada insight.
   - Las decisiones cerradas se registran en `action-register.md`, `change-log.md` e `interventions/`.

11. **Cerrar revision**
   - Se elige generar reporte Markdown, Markdown + PDF o cerrar sin reporte.
   - El reporte final se escribe en `governance/reports/governance-report.md`.

---

## Que archivos genera

```text
governance/
  README.md
  governance-config.md
  system-context.md
  evidence/
    code.md
    documentation.md
    versioning.md
    agents.md
    specialized/
      index.md
      security.md
      qa.md
      data.md
      performance.md
      compliance.md
  decisions.md
  change-log.md
  technical-debt.md
  action-register.md
  interventions/
  reports/
    governance-report.md
    generated/
  assets/
    architecture.dot
```

### Archivos principales

| Archivo | Uso |
|---|---|
| `governance-config.md` | Configuracion, alcance, permisos y recursos disponibles. |
| `system-context.md` | Vision resumida del sistema y flujos principales. |
| `evidence/*.md` | Evidencia por capas. |
| `evidence/specialized/*.md` | Senales potenciales que pueden requerir revision especializada. |
| `decisions.md` | Decisiones encontradas, inferidas, faltantes o contradictorias. |
| `technical-debt.md` | Deuda tecnica formal, solo en modo `profundo`. |
| `action-register.md` | Insights accionables y estado de decision. |
| `change-log.md` | Decisiones tomadas durante correcciones o intervenciones. |
| `interventions/` | Registro de cada insight corregido, pospuesto, descartado o derivado. |
| `reports/governance-report.md` | Reporte final de cierre. |
| `reports/generated/` | PDFs u otras salidas generadas. |

---

## Uso en Codex

Coloca la carpeta en la ruta de skills de Codex, por ejemplo:

```text
~/.codex/skills/gobernanza-por-evidencia
```

Abre Codex en la raiz del proyecto y pide:

```text
Usa la skill gobernanza-por-evidencia para revisar este repositorio.
Modo profundo, audiencia tecnico, permisos seguro, alcance repo completo.
```

---

## Uso en OpenCode

Puedes exponer la carpeta al proyecto o guardarla en la ruta de skills/instrucciones que uses para OpenCode.

Ejemplo de pedido:

```text
Lee gobernanza-por-evidencia/SKILL.md y realiza una revision de gobernanza por evidencia.
Modo: profundo.
Audiencia: tecnico.
Permisos: seguro.
Alcance: repo completo.
```

Recomendaciones:

- abrir OpenCode en la raiz del proyecto revisado;
- usar un solo agente responsable;
- no usar subagentes para esta skill;
- no instalar MCPs, plugins ni herramientas desde la revision;
- ejecutar scripts con `--quiet`;
- evitar salidas largas en pantalla.

OpenCode puede mostrar trazas o paneles internos del cliente. La skill reduce su propia salida, pero no controla toda la interfaz.

---

## Uso en OpenClaude u otros clientes

Si el cliente soporta skills locales, registra o adjunta la carpeta `gobernanza-por-evidencia/`.

Si no soporta skills, adjunta `SKILL.md` y la carpeta completa, o indica la ruta local donde existe.

Prompt minimo:

```text
Actua segun gobernanza-por-evidencia/SKILL.md.
Revisa este repositorio con evidencia escrita.
Guarda todo en governance/.
No modifiques codigo fuente durante la revision base.
Usa scripts con --quiet.
```

---

## Decisiones y botones

Cuando el cliente tenga botones u opciones, deben usarse para decisiones criticas:

- configuracion inicial;
- seleccion de insights;
- autorizacion de correcciones;
- derivacion especializada;
- cierre y tipo de reporte.

Opciones normales de insight:

```text
Corregir seguro
Posponer
Descartar
Requiere especialista
```

Para seguridad o `SEC-POT-*`, no usar `Corregir seguro`:

```text
Requiere especialista
Posponer
Descartar
```

---

## Reglas importantes

- No modificar codigo fuente durante la revision base.
- No tocar produccion.
- No usar `sudo`.
- No ejecutar comandos destructivos.
- No pedir ni guardar tokens.
- No instalar herramientas, MCPs, plugins ni subagentes.
- No usar rutas absolutas en evidencia, reportes o salidas generadas.
- No usar scripts improvisados para reescribir `governance/`.
- Si falta una herramienta o recurso, registrar `no disponible` y continuar.
- Si falta evidencia, registrar `no encontrado`, donde se busco y como afecta la confianza.

---

## Solucion de problemas

### El validador falla por deuda tecnica

Los campos enumerados deben contener solo valores limpios.

Correcto:

```md
**Interes esperado:** alto
```

Incorrecto:

```md
**Interes esperado:** alto (si se despliega en produccion)
```

La explicacion va en `Impacto de deuda`, `Viabilidad de pago`, `Contexto faltante` o `Evidencia`.

### El validador falla por `SEC-POT`

Las senales de seguridad no se corrigen directamente desde esta skill. Usa `Requiere especialista`, `Posponer` o `Descartar`.

### No se genera el reporte

Revisa que:

- `validate_governance.py --strict` pase;
- no existan insights en `pendiente de decision`;
- el reporte se base solo en archivos de `governance/`.

### No hay Docker, tests, GitHub CLI o MCPs

No se instalan. La revision continua con evidencia local y registra `no disponible` cuando corresponda.
