#!/usr/bin/env python3
"""Create the governance scaffold for evidence-based repository reviews."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


SOURCE_TEMPLATE = """# Evidence: {title}

## 1. Estado de fuente

**Estado:** pendiente / revisado / parcial / no encontrado
**Buscado en:** pendiente
**Cobertura:** pendiente
**Efecto en la revision:** pendiente
**Continuidad:** pendiente

## 2. Resumen util

- Pendiente.

## 3. Hallazgos

| ID | Afirmacion | Evidencia | Confianza | Impacto | Destino |
|---|---|---|---|---|---|

## 4. Flujos detectados

| ID | Flujo | Evidencia | Confianza | Destino |
|---|---|---|---|---|

## 5. Decisiones detectadas o inferidas

| ID | Decision | Tipo | Evidencia | Confianza | Pregunta |
|---|---|---|---|---|---|

## 6. Contradicciones y ausencias relevantes

| ID | Tipo | Descripcion | Evidencia | Efecto | Continuidad |
|---|---|---|---|---|---|

## 7. Preguntas utiles

- Pendiente.

## 8. Comandos relevantes

| Comando | Proposito | Resultado resumido |
|---|---|---|

## 9. Actualizaciones

- Fecha/hora: {timestamp}
- Cambio: archivo inicial creado.
- Motivo: inicio de revision.
"""


SPECIALIZED_TEMPLATE = """# Specialized Evidence: {title}

Este archivo registra senales potenciales. No confirma amenazas, vulnerabilidades, fallos QA,
incumplimientos ni problemas especializados sin evidencia directa.

## Estado

**Estado:** pendiente
**Buscado en:** pendiente
**Efecto en la revision:** pendiente
**Continuidad:** pendiente

## Senales potenciales

Pendiente.

## Formato requerido

```md
### {prefix}-POT-001: Titulo corto

**Estado:** potencial / descartado / requiere especialista / confirmado por evidencia directa
**Tipo:** {kind}
**Senal observada:**
**Evidencia:**
**Fuente relacionada:**
**Impacto potencial:** bajo / medio / alto
**Confianza:** baja / media / alta
**Por que requiere revision especializada:**
**No afirmar:** amenaza, explotabilidad, fallo o incumplimiento confirmado sin evidencia directa.
**Puede convertirse en deuda tecnica:** si / no / pendiente
**Accion sugerida:**
```

## Actualizaciones

- Fecha/hora: {timestamp}
- Cambio: archivo inicial creado.
- Motivo: preparar evidencia especializada extensible.
"""


def write_once(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def display_path(path: Path | str, root: Path) -> str:
    path = Path(path)
    if not path.is_absolute():
        path = (root / path).resolve()
    try:
        relative = path.resolve().relative_to(root)
    except ValueError:
        return "fuera del alcance revisado"
    text = str(relative).replace("\\", "/")
    return text or "."


def build_files(args: argparse.Namespace, root: Path) -> dict[str, str]:
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    debt_rule = (
        "Evaluacion formal habilitada. Leer criterios de deuda tecnica antes de registrar TD."
        if args.depth == "profundo"
        else "Evaluacion formal deshabilitada. Registrar solo senales o candidatos sin scoring formal."
    )
    review_path = display_path(args.review_path, root)

    return {
        "README.md": """# Governance

Base de gobernanza por evidencia para agentes y usuarios.

## Lectura rapida

- Configuracion y permisos: `governance-config.md`
- Contexto arc42 reducido: `system-context.md`
- Evidencia base: `evidence/`
- Evidencia especializada potencial: `evidence/specialized/`
- Decisiones ADR/MADR: `decisions.md`
- Decisiones tomadas en intervenciones: `change-log.md`
- Deuda tecnica: `technical-debt.md`
- Acciones e insights: `action-register.md`
- Intervenciones seleccionadas: `interventions/`
- Resumen de cierre: `reports/governance-report.md`
- PDFs y salidas finales: `reports/generated/`
- Diagrama de arquitectura: `assets/architecture.dot` y `assets/architecture.png` si se genera.

La evidencia especializada no confirma amenazas, fallos QA ni incumplimientos sin evidencia directa.
""",
        "governance-config.md": f"""# Governance Config

## Alcance
- Tipo: {args.scope}
- Ruta revisada: {review_path}
- Exclusiones: {args.exclusions or "pendiente"}

## Profundidad
- {args.depth}

## Audiencia
- {args.audience}

## Permisos
- {args.permissions}

## Recursos disponibles
- Repositorio local: disponible por defecto para lectura.
- Historial local: pendiente.
- Repositorio remoto: pendiente.
- Documentacion externa: pendiente.
- Verificacion local: pendiente.
- Entorno local: pendiente.
- Reportes existentes: pendiente.
- Revision especializada: pendiente.

## Checklist de revision
- [x] Preparar revision
- [ ] Explorar base
- [ ] Entender sistema
- [ ] Revisar evidencia
- [ ] Reconstruir decisiones
- [ ] Evaluar deuda si aplica
- [ ] Cerrar revision

## Reglas operativas
- No modificar codigo fuente durante la revision base.
- No tocar produccion.
- No usar sudo.
- No ejecutar comandos destructivos.
- Registrar comandos relevantes.
- Guardar evidencia en `governance/`.
- Deuda tecnica: {debt_rule}
- Credenciales: no pedir, imprimir ni guardar tokens o secretos.

## Estado de revision
- Iniciada: {timestamp}
- Ultima actualizacion: {timestamp}
- Pendiente: completar exploracion base, contexto, evidencia, decisiones, acciones y validacion.
""",
        "system-context.md": f"""# System Context

## 1. Proposito del sistema

Pendiente.

## 2. Alcance de revision

{args.scope}

## 3. Stakeholders o audiencias inferidas

Pendiente.

## 4. Restricciones detectadas

Pendiente.

## 5. Contexto del sistema

Pendiente.

## 6. Building blocks principales

| ID | Bloque | Ubicacion | Responsabilidad | Evidencia | Confianza |
|---|---|---|---|---|---|

## 7. Flujos principales

| ID | Flujo | Entrada | Salida | Modulos | Regla de negocio | Evidencia | Confianza | Preguntas |
|---|---|---|---|---|---|---|---|---|

## 8. Vista de despliegue/configuracion

Pendiente.

## 9. Conceptos transversales

Pendiente.

## 10. Decisiones existentes encontradas

Pendiente.

## 11. Calidad, riesgos y deuda declarada

Pendiente.

## 12. Glosario minimo

Pendiente.

## 13. Limitaciones

| ID | Limitacion | Buscado en | Efecto | Continuidad |
|---|---|---|---|---|

## 14. Historial de actualizacion

- Fecha/hora: {timestamp}
- Que cambio: archivo inicial creado.
- Por que: inicio de revision.
""",
        "evidence/code.md": SOURCE_TEMPLATE.format(title="code", timestamp=timestamp),
        "evidence/documentation.md": SOURCE_TEMPLATE.format(title="documentation", timestamp=timestamp),
        "evidence/versioning.md": SOURCE_TEMPLATE.format(title="versioning", timestamp=timestamp),
        "evidence/agents.md": SOURCE_TEMPLATE.format(title="agents", timestamp=timestamp),
        "evidence/specialized/index.md": f"""# Specialized Evidence Index

## Proposito

Resumen de senales potenciales que pueden requerir revision especializada.

## Regla de lenguaje

No afirmar amenazas, vulnerabilidades explotables, fallos QA, problemas de datos, performance o compliance sin evidencia directa.

## Conteos

| Tipo | Archivo | Conteo | Estado |
|---|---|---:|---|
| Security | `security.md` | 0 | pendiente |
| QA | `qa.md` | 0 | pendiente |
| Data | `data.md` | 0 | pendiente |
| Performance | `performance.md` | 0 | pendiente |
| Compliance | `compliance.md` | 0 | pendiente |

## Actualizaciones

- Fecha/hora: {timestamp}
- Cambio: indice inicial creado.
""",
        "evidence/specialized/security.md": SPECIALIZED_TEMPLATE.format(
            title="security", prefix="SEC", kind="security", timestamp=timestamp
        ),
        "evidence/specialized/qa.md": SPECIALIZED_TEMPLATE.format(
            title="qa", prefix="QA", kind="qa", timestamp=timestamp
        ),
        "evidence/specialized/data.md": SPECIALIZED_TEMPLATE.format(
            title="data", prefix="DATA", kind="data", timestamp=timestamp
        ),
        "evidence/specialized/performance.md": SPECIALIZED_TEMPLATE.format(
            title="performance", prefix="PERF", kind="performance", timestamp=timestamp
        ),
        "evidence/specialized/compliance.md": SPECIALIZED_TEMPLATE.format(
            title="compliance", prefix="COMP", kind="compliance", timestamp=timestamp
        ),
        "decisions.md": f"""# Decisions

## 1. Criterio usado

Registrar decisiones que afecten arquitectura, dependencia, flujo principal, persistencia, configuracion critica, integracion, deuda aceptada o evolucion futura.

## 2. Decisiones documentadas

| ID | Decision | Categoria | Fuente | Evidencia | Estado | Confianza |
|---|---|---|---|---|---|---|

## 3. Decisiones inferidas

| ID | Decision inferida | Categoria | Evidencia | Por que se infiere | Confianza | Pregunta pendiente |
|---|---|---|---|---|---|---|

Usar `Pregunta pendiente: no necesaria` cuando la evidencia escrita sea suficiente. Preguntar solo si la respuesta humana puede cambiar interpretacion, prioridad, alcance, deuda, handoff especializado o accion.

## 4. Decisiones faltantes

| ID | Decision faltante | Por que deberia documentarse | Evidencia | Accion sugerida |
|---|---|---|---|---|

## 5. Decisiones contradictorias

| ID | Contradiccion | Fuente A | Fuente B | Impacto | Accion sugerida |
|---|---|---|---|---|---|

## 6. ADRs retrospectivos sugeridos

| ID | Titulo sugerido | Decision relacionada | Prioridad | Estado |
|---|---|---|---|---|

## 7. Preguntas de validacion humana

Pendiente.

## 8. Fichas MADR retrospectivas sugeridas

Pendiente.

## 9. Actualizaciones

- Fecha/hora: {timestamp}
- Cambio: archivo inicial creado.
""",
        "change-log.md": """# Change Log

## Proposito

Registrar decisiones tomadas durante intervenciones o correcciones posteriores. No reemplaza `decisions.md`, que registra decisiones del sistema encontradas o inferidas durante la revision.

## Decisiones tomadas durante intervenciones

| ID | Fecha | Cambio/intervencion | Decision tomada | Motivo | Evidencia usada | Impacto documental | Archivos actualizados |
|---|---|---|---|---|---|---|---|
""",
        "technical-debt.md": f"""# Technical Debt

## 1. Criterio usado

Modo configurado: `{args.depth}`.

{debt_rule}

La deuda tecnica requiere constructo tecnico concreto, escenario de cambio, interes al cambiar, evidencia y decision de gestion.

## 2. Resumen

- Total de deudas confirmadas:
- Total de deudas probables:
- Total de deudas aceptadas temporalmente:
- Casos con evidencia insuficiente:
- Zonas mas afectadas:

## 3. Deudas

Pendiente.

## 4. Formato en modo profundo

```md
### TD-001: Titulo corto

**Estado:** candidata / probable / confirmada / aceptada / planificada / en pago / pagada / rechazada
**Tipo:** requisitos / arquitectura / diseno / codigo / pruebas / build / dependencias / documentacion / datos
**Origen:** deliberada / inadvertida / contingente / desconocida
**Artefacto afectado:**
**Decision relacionada:**
**Flujo afectado:** FLW- / no identificado
**Escenario de cambio:**
**Constructo que encarece el cambio:**
**Interes actual:** bajo / medio / alto
**Interes esperado:** bajo / medio / alto
**Probabilidad de interes:** baja / media / alta
**Costo de pago / principal:** bajo / medio / alto
**Beneficio de pago:** bajo / medio / alto
**Costo de no pagar:** bajo / medio / alto
**Impacto en evolucion:** bajo / medio / alto
**Impacto en mantenibilidad:** bajo / medio / alto
**Confianza de evidencia:** baja / media / alta
**Impacto de deuda:**
**Viabilidad de pago:**
**Prioridad estimada:** baja / media / alta / critica
**Evidencia:**
**Evidencia especializada relacionada:** SEC-POT / QA-POT / DATA-POT / PERF-POT / COMP-POT / ninguna
**Contexto faltante:**
**Pregunta al usuario:**
**Decision critica:** si
**Metodo requerido:** request_user_input
**Opciones permitidas:** pagar ahora / pagar con feature / planificar / aceptar temporalmente / monitorear / rechazar
**Decision de gestion:** pagar ahora / pagar con feature / planificar / aceptar temporalmente / monitorear / rechazar
**Fecha de revision:**
```

Los campos con listas de valores deben contener solo un valor permitido. No escribir `alto (explicacion)` ni `datos / seguridad`; poner la explicacion en campos narrativos.
""",
        "action-register.md": """# Action Register

## Proposito

Registrar insights accionables para seleccion del usuario antes del reporte final.

## Acciones

| ID | Insight | Tipo | Criticidad | Flujo afectado | Contexto faltante | Pregunta al usuario | Evidencia actual | Siguiente paso | Decision critica | Metodo requerido | Opciones permitidas | Decision usuario | Resultado | Intervencion | Estado final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Opciones de decision

- Corregir seguro
- Posponer
- Descartar
- Requiere especialista

Para acciones de seguridad o `SEC-POT-*`, no usar `Corregir seguro`; opciones validas: `Requiere especialista`, `Posponer`, `Descartar`.

## Metodo requerido

- Para decisiones criticas: `request_user_input`
- Para detalles no decisionales: texto libre despues de una seleccion

## Estados finales

- pendiente de decision
- corregido
- pospuesto
- descartado
- handoff especialista

## Regla de preguntas

Cada pregunta debe explicar que contexto falta, por que importa, que evidencia existe y que flujo afecta. No usar preguntas genericas como "que hago?".
""",
        "interventions/ACT-000-template.md": """# Intervention ACT-XXX

## Insight seleccionado

- ID:
- Insight:
- Decision usuario: Corregir seguro / Posponer / Descartar / Requiere especialista
- Metodo de decision: request_user_input
- Opciones presentadas:
- Alcance autorizado:

## Evidencia usada

Pendiente.

## Cambio aplicado o razon de no aplicar

Pendiente.

## Archivos tocados

Pendiente.

## Validacion ejecutada

Pendiente.

## Impacto documental

Pendiente.

## Actualizaciones requeridas

- action-register.md:
- change-log.md:
- evidence:
- report:
""",
        "reports/governance-report.md": """# Informe de Gobernanza por Evidencia

No completar este informe desde memoria. Generarlo solo despues de leer los archivos de `governance/`.

## 0. Configuracion del informe

- Audiencia: {audience}
- Nota: la audiencia adapta solo la presentacion del informe; no cambia el proceso, la evidencia ni las conclusiones.

## 1. Lectura rapida

| Item | Estado | Evidencia | Por que importa |
|---|---|---|---|

## 2. Semaforo de gobernanza

| Area | Estado | Confianza | Evidencia | Accion |
|---|---|---|---|---|
| Sistema | pendiente | pendiente | governance/system-context.md | pendiente |
| Documentacion | pendiente | pendiente | governance/evidence/documentation.md | pendiente |
| Versionado | pendiente | pendiente | governance/evidence/versioning.md | pendiente |
| Agentes | pendiente | pendiente | governance/evidence/agents.md | pendiente |
| Deuda tecnica | pendiente | pendiente | governance/technical-debt.md | pendiente |
| Revision especializada | pendiente | pendiente | governance/evidence/specialized/ | pendiente |

## 3. Decisiones o preguntas que requieren atencion

| ID | Tema | Pregunta o decision | Impacto | Evidencia |
|---|---|---|---|---|

## 4. Mapa actual del sistema

## 5. Fuentes revisadas

## 6. Decisiones relevantes

## 7. Hallazgos confirmados

## 8. Evidencia especializada potencial

## 9. Deuda tecnica

## 10. Preguntas abiertas

## 11. Acciones recomendadas

## 12. Evidencia usada
""".format(audience=args.audience),
        "assets/architecture.dot": """digraph architecture {
  label="Architecture evidence pending";
  labelloc="t";
}
""",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository or project root.")
    parser.add_argument("--depth", required=True, choices=["normal", "profundo"])
    parser.add_argument("--audience", required=True, choices=["tecnico", "jefatura"])
    parser.add_argument("--permissions", required=True, choices=["seguro", "herramientas"])
    parser.add_argument("--scope", required=True)
    parser.add_argument("--review-path", default=".")
    parser.add_argument("--exclusions", default="")
    parser.add_argument("--quiet", action="store_true", help="Print only a compact completion summary.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    governance_dir = root / "governance"
    created: list[str] = []
    skipped: list[str] = []

    for relative, content in build_files(args, root).items():
        target = governance_dir / relative
        if write_once(target, content):
            created.append(str(target.relative_to(root)))
        else:
            skipped.append(str(target.relative_to(root)))

    for relative in ["interventions", "reports/generated"]:
        path = governance_dir / relative
        path.mkdir(parents=True, exist_ok=True)

    if args.quiet:
        print(f"Governance initialized: {display_path(governance_dir, root)} (created {len(created)}, skipped {len(skipped)})")
    else:
        print(f"Governance directory: {display_path(governance_dir, root)}")
        print(f"Created: {len(created)}")
        for item in created:
            print(f"  + {item}")
        if skipped:
            print(f"Skipped existing: {len(skipped)}")
            for item in skipped:
                print(f"  = {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
