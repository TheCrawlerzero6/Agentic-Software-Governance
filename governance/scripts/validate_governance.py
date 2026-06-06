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
    "interventions/ACT-000-template.md",
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

ACTION_ALLOWED_DECISIONS = {
    "pendiente de decision",
    "corregir seguro",
    "posponer",
    "descartar",
    "requiere especialista",
}

ACTION_SELECTABLE_DECISIONS = ACTION_ALLOWED_DECISIONS - {"pendiente de decision"}
ACTION_SECURITY_DECISIONS = {"posponer", "descartar", "requiere especialista"}

ACTION_ALLOWED_FINAL_STATES = {
    "pendiente de decision",
    "corregido",
    "pospuesto",
    "descartado",
    "handoff especialista",
}

ACTION_CRITICAL_VALUES = {"si", "no"}

ACTION_REQUIRED_METHODS = {"request_user_input", "texto libre despues de una seleccion"}

EMPTY_VALUES = {"", "-", "pendiente", "no encontrado"}

ABSOLUTE_MACHINE_PATH_PATTERNS = [
    r"(?<![\w.-])/home/[^`\s|)]+",
    r"(?<![\w.-])/tmp/[^`\s|)]+",
    r"(?<![\w.-])/var/[^`\s|)]+",
    r"(?<![\w.-])/Users/[^`\s|)]+",
    r"\b[A-Za-z]:\\[^`\s|)]+",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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


def action_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
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
        rows.append(cells)
    return rows


def split_allowed_options(text: str) -> set[str]:
    return {
        option.strip().lower()
        for option in re.split(r"\s*/\s*|[,;]", text)
        if option.strip()
    }


def action_is_security_signal(cells: list[str]) -> bool:
    lowered = " | ".join(cells).lower()
    return "sec-pot" in lowered or "evidence/specialized/security" in lowered or (len(cells) > 2 and cells[2].lower() in {"seguridad", "security"})


def action_register_context_errors(text: str) -> list[str]:
    errors: list[str] = []
    field_names = [
        "ID",
        "Insight",
        "Tipo",
        "Criticidad",
        "Flujo afectado",
        "Contexto faltante",
        "Pregunta al usuario",
        "Evidencia actual",
        "Siguiente paso",
        "Decision critica",
        "Metodo requerido",
        "Opciones permitidas",
        "Decision usuario",
        "Resultado",
        "Intervencion",
        "Estado final",
    ]
    for cells in action_rows(text):
        action_id = cells[0] if cells else "fila sin ID"
        if len(cells) < 16:
            errors.append(f"action-register.md {action_id} must use the 16-column action schema")
            continue
        required_indexes = [4, 5, 6, 7, 8, 9, 10, 11]
        for index in required_indexes:
            if cells[index].lower() in EMPTY_VALUES:
                errors.append(f"action-register.md {action_id} missing required field: {field_names[index]}")
        critical = cells[9].lower()
        method = cells[10].lower()
        options = cells[11].lower()
        decision = cells[12].lower()
        final_state = cells[15].lower()
        if critical not in ACTION_CRITICAL_VALUES:
            errors.append(f"action-register.md {action_id} has invalid Decision critica: {cells[9]}")
        if method not in ACTION_REQUIRED_METHODS:
            errors.append(f"action-register.md {action_id} has invalid Metodo requerido: {cells[10]}")
        if critical == "si" and method != "request_user_input":
            errors.append(f"action-register.md {action_id} critical decisions must use request_user_input")
        allowed_decisions = ACTION_SECURITY_DECISIONS if action_is_security_signal(cells) else ACTION_SELECTABLE_DECISIONS
        if critical == "si":
            option_set = split_allowed_options(options)
            if not option_set or not option_set.issubset(allowed_decisions):
                errors.append(f"action-register.md {action_id} Opciones permitidas must be a valid subset of: {', '.join(sorted(allowed_decisions))}")
        if decision not in ACTION_ALLOWED_DECISIONS:
            errors.append(f"action-register.md {action_id} has invalid Decision usuario: {cells[12]}")
        if decision != "pendiente de decision" and decision not in split_allowed_options(options):
            errors.append(f"action-register.md {action_id} Decision usuario must be included in Opciones permitidas")
        if final_state not in ACTION_ALLOWED_FINAL_STATES:
            errors.append(f"action-register.md {action_id} has invalid Estado final: {cells[15]}")
    return errors


def action_register_has_security_correction(text: str) -> bool:
    for cells in action_rows(text):
        if not action_is_security_signal(cells):
            continue
        decision = cells[12].lower() if len(cells) > 12 else ""
        action_text = " | ".join(
            value for index, value in enumerate(cells)
            if index in {8, 12, 13}
        ).lower()
        if decision == "corregir seguro" or re.search(r"\b(corregir|arreglar|parchar|patch|mitigar|remediar|implementar)\b", action_text):
            return True
    return False


def action_register_has_pending_decisions(text: str) -> bool:
    for cells in action_rows(text):
        if len(cells) < 16:
            return True
        decision = cells[12].lower()
        final_state = cells[15].lower()
        if decision == "pendiente de decision" or final_state == "pendiente de decision":
            return True
    return False


def action_register_closed_rows_invalid(text: str, governance: Path) -> list[str]:
    errors: list[str] = []
    change_log_text = read(governance / "change-log.md") if (governance / "change-log.md").exists() else ""
    for cells in action_rows(text):
        if len(cells) < 16:
            continue
        action_id = cells[0]
        decision = cells[12].lower()
        result = cells[13].lower()
        intervention = cells[14]
        final_state = cells[15].lower()
        if decision == "pendiente de decision" or final_state == "pendiente de decision":
            continue
        if result in EMPTY_VALUES:
            errors.append(f"{action_id} closed insight must include Resultado")
        if not intervention or intervention.lower() in EMPTY_VALUES:
            errors.append(f"{action_id} closed insight must include Intervencion")
            continue
        if not intervention.startswith("governance/interventions/") and not intervention.startswith("interventions/"):
            errors.append(f"{action_id} Intervencion must point to interventions/ACT-XXX.md")
        else:
            intervention_path = governance.parent / intervention if intervention.startswith("governance/") else governance / intervention
            if not intervention_path.exists():
                errors.append(f"{action_id} Intervencion file does not exist: {intervention}")
        if action_id not in change_log_text and intervention not in change_log_text:
            errors.append(f"{action_id} closed insight must be recorded in change-log.md")
        if decision == "corregir seguro" and final_state != "corregido":
            errors.append(f"{action_id} with Corregir seguro must end as corregido")
        if decision == "posponer" and final_state != "pospuesto":
            errors.append(f"{action_id} with Posponer must end as pospuesto")
        if decision == "descartar" and final_state != "descartado":
            errors.append(f"{action_id} with Descartar must end as descartado")
        if decision == "requiere especialista" and final_state != "handoff especialista":
            errors.append(f"{action_id} with Requiere especialista must end as handoff especialista")
    return errors


def inferred_decisions_invalid(text: str) -> bool:
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
        if len(cells) < 7:
            return True
        evidence = cells[3].lower()
        reason = cells[4].lower()
        confidence = cells[5].lower()
        question = cells[6].lower()
        if evidence in {"", "-", "pendiente", "no encontrado"}:
            return True
        if reason in {"", "-", "pendiente", "no encontrado"}:
            return True
        if confidence not in {"baja", "media", "alta"}:
            return True
        if question in {"", "-", "pendiente", "no encontrado"}:
            return True
        if confidence == "baja" and question in {"no necesaria", "no aplica"}:
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


def enum_has_inline_explanation(value: str, allowed: set[str]) -> bool:
    lowered = value.lower().strip()
    return any(
        lowered.startswith(f"{option} (") or lowered.startswith(f"{option}/") or lowered.startswith(f"{option} /")
        for option in allowed
    )


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


def absolute_machine_path_hits(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in ABSOLUTE_MACHINE_PATH_PATTERNS:
        hits.extend(re.findall(pattern, text))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository or project root.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when required evidence files still look like placeholders.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print a compact success summary; errors remain explicit.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    governance = root / "governance"
    errors: list[str] = []
    warnings: list[str] = []

    if not governance.is_dir():
        print(f"ERROR: missing {display_path(governance, root)}")
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

    for path in list(governance.rglob("*.md")) + list(governance.rglob("*.dot")):
        hits = absolute_machine_path_hits(read(path))
        if hits:
            sample = hits[0]
            errors.append(f"{display_path(path, root)} contains absolute machine path: {sample}")

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
    if decisions_path.exists() and inferred_decisions_invalid(read(decisions_path)):
        errors.append("inferred decisions must include evidence, inference reason, confidence, and a needed question or 'no necesaria'")

    action_path = governance / "action-register.md"
    action_text = read(action_path) if action_path.exists() else ""
    if action_text:
        errors.extend(action_register_context_errors(action_text))
    if action_text and action_register_has_security_correction(action_text):
        errors.append("action-register.md must not propose direct correction for SEC-POT actions")
    if action_text:
        errors.extend(action_register_closed_rows_invalid(action_text, governance))

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
                    "Decision critica",
                    "Metodo requerido",
                    "Opciones permitidas",
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
                        value = field_value(record, field)
                        if enum_has_inline_explanation(value, allowed):
                            errors.append(f"TD record has invalid {field}: enum fields must contain only the allowed value, move explanation elsewhere: {value}")
                        else:
                            errors.append(f"TD record has invalid {field}: {value}")

                critical = field_lower(record, "Decision critica")
                method = field_lower(record, "Metodo requerido")
                options = field_lower(record, "Opciones permitidas")
                if critical not in ACTION_CRITICAL_VALUES:
                    errors.append(f"TD record has invalid Decision critica: {field_value(record, 'Decision critica')}")
                if critical == "si" and method != "request_user_input":
                    errors.append("TD critical management decision must use request_user_input")
                if critical == "si":
                    option_set = split_allowed_options(options)
                    management_decision = field_lower(record, "Decision de gestion")
                    if not option_set or not option_set.issubset(TD_ALLOWED_DECISIONS):
                        errors.append("TD critical management options must be a valid subset of allowed options")
                    elif management_decision not in option_set:
                        errors.append("TD critical management decision must be included in Opciones permitidas")

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
        if not placeholder and action_text and action_register_has_pending_decisions(action_text):
            errors.append("reports/governance-report.md cannot be finalized while action-register.md has pending insight decisions")

    if permissions == "seguro":
        commands_text = "\n".join(
            read(governance / relative)
            for relative in SOURCE_FILES
            if (governance / relative).exists()
        )
        if re.search(r"\b(npm test|pytest|docker compose up|npm install|pip install)\b", commands_text):
            warnings.append("seguro mode contains commands that may require herramientas authorization")

    if warnings and not args.quiet:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    if args.quiet:
        warning_text = f", warnings: {len(warnings)}" if warnings else ""
        print(f"Governance validation passed ({depth or 'unknown'}, {audience or 'unknown'}, {permissions or 'unknown'}{warning_text}).")
    else:
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
