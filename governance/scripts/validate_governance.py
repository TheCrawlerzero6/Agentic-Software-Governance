#!/usr/bin/env python3
"""Validate a governance folder before writing the final report."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED = [
    "README.md",
    "governance-config.md",
    "system-context.md",
    "evidence/code.md",
    "evidence/documentation.md",
    "evidence/versioning.md",
    "evidence/agents.md",
    "evidence/specialized/index.md",
    "evidence/specialized/security.md",
    "evidence/specialized/qa.md",
    "evidence/specialized/data.md",
    "evidence/specialized/performance.md",
    "evidence/specialized/compliance.md",
    "decisions.md",
    "change-log.md",
    "technical-debt.md",
    "action-register.md",
    "reports/governance-report.md",
]

REQUIRED_DIRS = [
    "reports/generated",
]

SOURCE_FILES = [
    "evidence/code.md",
    "evidence/documentation.md",
    "evidence/versioning.md",
    "evidence/agents.md",
]

SPECIALIZED_FILES = [
    "evidence/specialized/security.md",
    "evidence/specialized/qa.md",
    "evidence/specialized/data.md",
    "evidence/specialized/performance.md",
    "evidence/specialized/compliance.md",
]

ABSOLUTE_SPECIALIZED_PATTERNS = [
    r"\bamenaza confirmada\b",
    r"\bvulnerabilidad explotable\b",
    r"\bfallo qa confirmado\b",
    r"\bfallo de qa confirmado\b",
    r"\bincumplimiento confirmado\b",
]

SECURITY_DIRECT_ACTION_PATTERNS = [
    r"\bcorregir\b",
    r"\barreglar\b",
    r"\bparchar\b",
    r"\bpatch\b",
    r"\bmitigar\b",
    r"\bremediar\b",
    r"\bactualizar dependencia\b",
    r"\bimplementar\b",
]

TD_ALLOWED_STATES = {
    "candidata",
    "probable",
    "confirmada",
    "aceptada",
    "planificada",
    "en pago",
    "pagada",
    "rechazada",
}

TD_ALLOWED_TYPES = {
    "requisitos",
    "arquitectura",
    "diseno",
    "codigo",
    "pruebas",
    "build",
    "dependencias",
    "documentacion",
    "datos",
}

TD_ALLOWED_ORIGINS = {
    "deliberada",
    "inadvertida",
    "contingente",
    "desconocida",
}

TD_LOW_MED_HIGH_MASC = {"bajo", "medio", "alto"}
TD_LOW_MED_HIGH_FEM = {"baja", "media", "alta"}
TD_ALLOWED_PRIORITIES = {"baja", "media", "alta", "critica"}
TD_ALLOWED_DECISIONS = {
    "pagar ahora",
    "pagar con feature",
    "planificar",
    "aceptar temporalmente",
    "monitorear",
    "rechazar",
}

TD_NON_DEBT_ISSUE_PATTERNS = [
    r"\bbug\b",
    r"\bdefecto\b",
    r"\berror funcional\b",
    r"\bvulnerabilidad\b",
    r"\bcve\b",
    r"\bfeature\b",
    r"\bfuncionalidad faltante\b",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def detect_config_value(config: str, heading: str, allowed: set[str]) -> str | None:
    pattern = rf"## {re.escape(heading)}\s*\n\s*-\s*([a-zA-Z_-]+)\b"
    match = re.search(pattern, config, re.IGNORECASE)
    if not match:
        return None
    value = match.group(1).lower()
    return value if value in allowed else None


def has_real_content(text: str) -> bool:
    body = re.sub(r"^#.*$", "", text, flags=re.MULTILINE)
    body = re.sub(r"\b(Pendiente|pendiente|no encontrado)\.?\b", "", body)
    body = re.sub(r"\|[-:\s|]+\|", "", body)
    return bool(body.strip())


def strip_fenced_blocks(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def strip_no_assertion_lines(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines()
        if not line.strip().lower().startswith("**no afirmar:**")
    )


def source_has_state(text: str) -> bool:
    return bool(re.search(r"\*\*Estado:\*\*\s*(revisado|parcial|no encontrado)\b", text, re.IGNORECASE))


def source_state(text: str) -> str:
    match = re.search(r"\*\*Estado:\*\*\s*(revisado|parcial|no encontrado)\b", text, re.IGNORECASE)
    return match.group(1).lower() if match else ""


def section_body(text: str, heading: str) -> str:
    pattern = rf"^##\s+\d+\.\s+{re.escape(heading)}\s*$"
    lines = text.splitlines()
    in_section = False
    body: list[str] = []
    for line in lines:
        if re.match(pattern, line.strip(), re.IGNORECASE):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            body.append(line)
    return "\n".join(body).strip()


def section_has_useful_content(text: str, heading: str) -> bool:
    body = section_body(text, heading)
    body = re.sub(r"\|[-:\s|]+\|", "", body)
    body = re.sub(r"\b(Pendiente|pendiente|no encontrado)\.?\b", "", body)
    body = body.replace("-", "").strip()
    return bool(body)


def source_findings_missing_evidence_or_confidence(text: str) -> bool:
    body = section_body(text, "Hallazgos")
    for line in body.splitlines():
        if not line.startswith("|"):
            continue
        lowered = line.lower()
        if "---" in lowered or "afirmacion" in lowered:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 6:
            return True
        evidence = cells[2].lower()
        confidence = cells[3].lower()
        if evidence in {"", "-", "pendiente", "no encontrado"}:
            return True
        if confidence not in {"baja", "media", "alta"}:
            return True
    return False


def table_rows_missing_evidence(text: str, section_heading: str) -> bool:
    in_section = False
    for line in text.splitlines():
        heading = line.strip().lower()
        if heading.startswith(section_heading.lower()):
            in_section = True
            continue
        if in_section and heading.startswith("## "):
            in_section = False
        if not in_section or not line.startswith("|"):
            continue
        lowered = line.lower()
        if "---" in lowered or "evidencia" in lowered:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 5 and cells[4].lower() in {"", "-", "pendiente", "no encontrado"}:
            return True
    return False


def action_register_missing_context(text: str) -> bool:
    in_actions = False
    for line in text.splitlines():
        heading = line.strip().lower()
        if heading.startswith("## acciones"):
            in_actions = True
            continue
        if in_actions and heading.startswith("## "):
            in_actions = False
        if not in_actions or not line.startswith("|"):
            continue
        lowered = line.lower()
        if "---" in lowered or "contexto faltante" in lowered:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 10:
            return True
        required_indexes = [4, 5, 6, 7]
        for index in required_indexes:
            if cells[index].lower() in {"", "-", "pendiente", "no encontrado"}:
                return True
    return False


def action_register_has_security_correction(text: str) -> bool:
    in_actions = False
    for line in text.splitlines():
        heading = line.strip().lower()
        if heading.startswith("## acciones"):
            in_actions = True
            continue
        if in_actions and heading.startswith("## "):
            in_actions = False
        if not in_actions or not line.startswith("|"):
            continue
        lowered = line.lower()
        if "---" in lowered or "evidencia" in lowered:
            continue
        if "sec-pot" in lowered and re.search(r"\b(corregir|arreglar|parchar|patch|mitigar|remediar|implementar)\b", lowered):
            return True
    return False


def inferred_decisions_missing_question(text: str) -> bool:
    in_inferred_section = False
    for line in text.splitlines():
        heading = line.strip().lower()
        if heading.startswith("## 3. decisiones inferidas"):
            in_inferred_section = True
            continue
        if in_inferred_section and heading.startswith("## "):
            in_inferred_section = False
        if not in_inferred_section or not line.startswith("|"):
            continue
        lowered = line.lower()
        if "---" in lowered or "pregunta pendiente" in lowered:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 6 and cells[-1] and cells[-1].lower() not in {"pendiente", "no encontrado", "-"}:
            continue
        return True
    return False


def specialized_records(text: str) -> list[str]:
    text = strip_fenced_blocks(text)
    records: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if re.match(r"^###\s+(SEC|QA|DATA|PERF|COMP)-POT-\d{3}\b", line):
            if current:
                records.append("\n".join(current))
            current = [line]
        elif current:
            current.append(line)
    if current:
        records.append("\n".join(current))
    return records


def field_value(record: str, field: str) -> str:
    match = re.search(rf"^\*\*{re.escape(field)}:\*\*\s*(.+)$", record, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def record_has_value(record: str, field: str) -> bool:
    value = field_value(record, field).lower()
    return bool(value and value not in {"pendiente", "-", "no encontrado"})


def field_lower(record: str, field: str) -> str:
    return field_value(record, field).lower()


def field_in_allowed(record: str, field: str, allowed: set[str]) -> bool:
    return field_lower(record, field) in allowed


def td_records(text: str) -> list[str]:
    text = strip_fenced_blocks(text)
    records: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if re.match(r"^###\s+TD-\d{3}\b", line):
            if current:
                records.append("\n".join(current))
            current = [line]
        elif current:
            current.append(line)
    if current:
        records.append("\n".join(current))
    return records


def td_record_mentions_non_debt_issue(record: str) -> bool:
    lowered = record.lower()
    return any(re.search(pattern, lowered) for pattern in TD_NON_DEBT_ISSUE_PATTERNS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository or project root.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when required evidence files still look like placeholders.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    governance = root / "governance"
    errors: list[str] = []
    warnings: list[str] = []

    if not governance.is_dir():
        print(f"ERROR: missing {governance}")
        return 1

    for relative in REQUIRED_DIRS:
        path = governance / relative
        if not path.is_dir():
            errors.append(f"missing directory {relative}")

    for relative in REQUIRED:
        path = governance / relative
        if not path.exists():
            errors.append(f"missing {relative}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {relative}")

    config_path = governance / "governance-config.md"
    depth = None
    audience = None
    permissions = None
    if config_path.exists():
        config = read(config_path)
        depth = detect_config_value(config, "Profundidad", {"normal", "profundo"})
        audience = detect_config_value(config, "Audiencia", {"tecnico", "jefatura"})
        permissions = detect_config_value(config, "Permisos", {"seguro", "herramientas"})
        if depth is None:
            errors.append("governance-config.md must declare '## Profundidad' as normal or profundo")
        if audience is None:
            errors.append("governance-config.md must declare '## Audiencia' as tecnico or jefatura")
        if permissions is None:
            errors.append("governance-config.md must declare '## Permisos' as seguro or herramientas")
        if "Recursos disponibles" not in config:
            errors.append("governance-config.md must include '## Recursos disponibles'")
        if "Checklist de revision" not in config:
            errors.append("governance-config.md must include '## Checklist de revision'")
        if "Credenciales" not in config:
            warnings.append("governance-config.md should document credential handling")

    evidence_files = ["system-context.md", *SOURCE_FILES, "decisions.md"]
    for relative in evidence_files:
        path = governance / relative
        if path.exists() and not has_real_content(read(path)):
            message = f"{relative} still appears to contain only placeholder content"
            if args.strict:
                errors.append(message)
            else:
                warnings.append(message)

    for relative in SOURCE_FILES:
        path = governance / relative
        if not path.exists():
            continue
        source_text = read(path)
        state = source_state(source_text)
        if not source_has_state(source_text):
            message = f"{relative} should set Estado de fuente to revisado, parcial, or no encontrado"
            if args.strict:
                errors.append(message)
            else:
                warnings.append(message)
        elif state != "no encontrado" and not section_has_useful_content(source_text, "Resumen util"):
            message = f"{relative} must include useful summary content when source state is {state}"
            if args.strict:
                errors.append(message)
            else:
                warnings.append(message)
        if source_findings_missing_evidence_or_confidence(source_text):
            errors.append(f"{relative} findings must include evidence and confidence baja/media/alta")

    decisions_path = governance / "decisions.md"
    if decisions_path.exists() and inferred_decisions_missing_question(read(decisions_path)):
        errors.append("inferred decisions must include a concrete pending validation question")

    action_path = governance / "action-register.md"
    if action_path.exists() and table_rows_missing_evidence(read(action_path), "## Acciones"):
        errors.append("action-register.md actions must include evidence")
    if action_path.exists() and action_register_missing_context(read(action_path)):
        errors.append("action-register.md actions must include affected flow, missing context, user question, and evidence")
    if action_path.exists() and action_register_has_security_correction(read(action_path)):
        errors.append("action-register.md must not propose direct correction for SEC-POT actions")

    for relative in SPECIALIZED_FILES:
        path = governance / relative
        if not path.exists():
            continue
        text = strip_fenced_blocks(read(path))
        language_text = strip_no_assertion_lines(text)
        lowered = language_text.lower()
        for pattern in ABSOLUTE_SPECIALIZED_PATTERNS:
            if re.search(pattern, lowered) and "confirmado por evidencia directa" not in lowered:
                errors.append(f"{relative} uses confirmed specialized-risk language without direct-evidence status")
                break
        for record in specialized_records(text):
            for field in ["Evidencia", "Accion sugerida"]:
                if not record_has_value(record, field):
                    errors.append(f"{relative} specialized record is missing {field}")
            if record.startswith("### SEC-POT-"):
                action = field_value(record, "Accion sugerida").lower()
                if any(re.search(pattern, action) for pattern in SECURITY_DIRECT_ACTION_PATTERNS):
                    errors.append(f"{relative} SEC-POT records must hand off to specialized review, not propose direct correction")
                if not re.search(r"revision especializada|especialista|skill|plugin", action):
                    errors.append(f"{relative} SEC-POT records must mention specialized review or an available skill/plugin")

    debt_path = governance / "technical-debt.md"
    if debt_path.exists():
        debt_text = read(debt_path)
        records = td_records(debt_text)
        has_score = bool(re.search(r"\bScore\b|Criticidad:|Prioridad estimada:|Impacto de deuda:", debt_text, re.IGNORECASE))
        if depth == "normal" and records:
            errors.append("normal mode must not contain formal TD entries in technical-debt.md")
        if depth == "normal" and has_score and records:
            errors.append("normal mode must not contain scoring for formal TD entries")
        if depth == "profundo":
            for record in records:
                required_fields = [
                    "Estado",
                    "Tipo",
                    "Origen",
                    "Artefacto afectado",
                    "Decision relacionada",
                    "Flujo afectado",
                    "Escenario de cambio",
                    "Constructo que encarece el cambio",
                    "Interes actual",
                    "Interes esperado",
                    "Probabilidad de interes",
                    "Costo de pago / principal",
                    "Beneficio de pago",
                    "Costo de no pagar",
                    "Impacto en evolucion",
                    "Impacto en mantenibilidad",
                    "Confianza de evidencia",
                    "Impacto de deuda",
                    "Viabilidad de pago",
                    "Prioridad estimada",
                    "Evidencia",
                    "Evidencia especializada relacionada",
                    "Contexto faltante",
                    "Pregunta al usuario",
                    "Decision de gestion",
                    "Fecha de revision",
                ]
                missing = [field for field in required_fields if not record_has_value(record, field)]
                if missing:
                    errors.append("TD records must include required fields: " + ", ".join(missing))
                    continue

                allowed_checks = [
                    ("Estado", TD_ALLOWED_STATES),
                    ("Tipo", TD_ALLOWED_TYPES),
                    ("Origen", TD_ALLOWED_ORIGINS),
                    ("Interes actual", TD_LOW_MED_HIGH_MASC),
                    ("Interes esperado", TD_LOW_MED_HIGH_MASC),
                    ("Probabilidad de interes", TD_LOW_MED_HIGH_FEM),
                    ("Costo de pago / principal", TD_LOW_MED_HIGH_MASC),
                    ("Beneficio de pago", TD_LOW_MED_HIGH_MASC),
                    ("Costo de no pagar", TD_LOW_MED_HIGH_MASC),
                    ("Impacto en evolucion", TD_LOW_MED_HIGH_MASC),
                    ("Impacto en mantenibilidad", TD_LOW_MED_HIGH_MASC),
                    ("Confianza de evidencia", TD_LOW_MED_HIGH_FEM),
                    ("Prioridad estimada", TD_ALLOWED_PRIORITIES),
                    ("Decision de gestion", TD_ALLOWED_DECISIONS),
                ]
                for field, allowed in allowed_checks:
                    if not field_in_allowed(record, field, allowed):
                        errors.append(f"TD record has invalid {field}: {field_value(record, field)}")

                if td_record_mentions_non_debt_issue(record):
                    litmus_fields = [
                        "Artefacto afectado",
                        "Escenario de cambio",
                        "Constructo que encarece el cambio",
                        "Interes actual",
                        "Interes esperado",
                    ]
                    if any(not record_has_value(record, field) for field in litmus_fields):
                        errors.append("bugs, vulnerabilities, or missing features can be TD only when construct and change-cost interest are documented")

                confidence = field_lower(record, "Confianza de evidencia")
                if confidence in {"baja", "media"}:
                    for field in ["Contexto faltante", "Pregunta al usuario"]:
                        if not record_has_value(record, field):
                            errors.append(f"TD record with low/medium confidence must include {field}")

                related = field_value(record, "Evidencia especializada relacionada")
                if related and related.lower() not in {"ninguna", "no", "pendiente", "-"}:
                    if not record_has_value(record, "Constructo que encarece el cambio") or not record_has_value(record, "Escenario de cambio"):
                        errors.append("specialized evidence can cross into TD only when construct and change scenario are explained")

    report_path = governance / "reports/governance-report.md"
    if report_path.exists():
        report = read(report_path)
        placeholder = "No completar este informe desde memoria" in report
        cites_governance = "governance/" in report
        required_headings = [
            "## 1. Lectura rapida",
            "## 2. Semaforo de gobernanza",
            "## 3. Decisiones o preguntas que requieren atencion",
        ]
        for heading in required_headings:
            if heading not in report:
                errors.append(f"reports/governance-report.md must include '{heading}'")
        if not placeholder and not cites_governance:
            errors.append("reports/governance-report.md must cite governance/ evidence files")
        if not placeholder and audience and audience not in report.lower():
            errors.append("reports/governance-report.md must declare the configured audience")

    if permissions == "seguro":
        commands_text = "\n".join(
            read(governance / relative)
            for relative in SOURCE_FILES
            if (governance / relative).exists()
        )
        if re.search(r"\b(npm test|pytest|docker compose up|npm install|pip install)\b", commands_text):
            warnings.append("seguro mode contains commands that may require herramientas authorization")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Governance validation passed.")
    if depth:
        print(f"Depth: {depth}")
    if audience:
        print(f"Audience: {audience}")
    if permissions:
        print(f"Permissions: {permissions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
