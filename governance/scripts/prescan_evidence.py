#!/usr/bin/env python3
"""Seed governance evidence files with non-mutating repository evidence."""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
from datetime import datetime, timezone
from pathlib import Path


EXCLUDED_DIRS = {
    ".git",
    ".governance",
    "governance",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".venv",
    "venv",
    "target",
    "coverage",
    "__pycache__",
}

MANIFEST_PATTERNS = [
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "Makefile",
    "requirements.txt",
]
LOCK_PATTERNS = ["package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "Cargo.lock"]
DOC_PATTERNS = ["README*", "docs/**", "doc/**", "architecture/**", "adr/**", "adrs/**", "madr/**"]
DOCKER_PATTERNS = ["Dockerfile*", "docker-compose*.yml", "docker-compose*.yaml", "compose*.yml", "compose*.yaml"]
AGENT_PATTERNS = ["AGENTS.md", ".agents/**", ".codex/**", "*prompt*", "*rules*"]
TEST_PATTERNS = ["*test*", "*spec*", "tests/**", "test/**", "__tests__/**"]
CONFIG_PATTERNS = ["*.env.example", "*.env.sample", "*config*", "*settings*", "*.toml", "*.yaml", "*.yml"]
DATA_PATTERNS = ["migrations/**", "migration/**", "schema.sql", "prisma/schema.prisma", "*schema*", "*model*"]
SATD_TERMS = ["TODO", "FIXME", "HACK", "WORKAROUND", "XXX", "temporary", "quick fix"]


def rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def visible_files(root: Path, limit: int) -> list[str]:
    items: list[str] = []
    for path in root.rglob("*"):
        if len(items) >= limit:
            break
        if path.is_dir():
            continue
        parts = set(path.relative_to(root).parts)
        if parts & EXCLUDED_DIRS:
            continue
        items.append(rel(path, root))
    return sorted(items)


def match_any(files: list[str], patterns: list[str], limit: int = 40) -> list[str]:
    matches: list[str] = []
    for file in files:
        for pattern in patterns:
            if fnmatch.fnmatch(file, pattern) or fnmatch.fnmatch(file.lower(), pattern.lower()):
                matches.append(file)
                break
    return matches[:limit]


def run_git(root: Path, args: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    return result.returncode == 0, result.stdout.strip()


def satd_hits(root: Path, files: list[str], limit: int = 20) -> list[str]:
    hits: list[str] = []
    for file in files:
        if len(hits) >= limit:
            break
        path = root / file
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".lock"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for term in SATD_TERMS:
            if term.lower() in text.lower():
                hits.append(f"{file}: contains {term}")
                break
    return hits


def bullet(items: list[str]) -> str:
    if not items:
        return "- no encontrado"
    return "\n".join(f"- `{item}`" for item in items)


def source_doc(title: str, prefix: str, status: str, searched: str, effect: str, continuity: str, body: str) -> str:
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return f"""# Evidence: {title}

## 1. Estado de fuente

**Estado:** {status}
**Buscado en:** {searched}
**Cobertura:** pre-scan automatico no mutante; requiere revision manual para conclusiones.
**Efecto en la revision:** {effect}
**Continuidad:** {continuity}

## 2. Resumen util

{body}

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
| {prefix}-ABS-001 | ausencia | Elementos no encontrados en pre-scan | {searched} | Ver resumen util | Se continua con revision manual |

## 7. Preguntas utiles

- Pendiente de revision manual si esta fuente afecta decisiones, deuda, riesgos o acciones.

## 8. Comandos relevantes

| Comando | Proposito | Resultado resumido |
|---|---|---|
| `prescan_evidence.py --root .` | Detectar evidencia inicial sin mutar codigo | {status} |

## 9. Actualizaciones

- Fecha/hora: {timestamp}
- Cambio: pre-scan inicial registrado.
- Motivo: preparar revision por evidencia.
"""


def specialized_doc(title: str, prefix: str, kind: str, signals: list[str], searched: str) -> str:
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    status = "parcial" if signals else "no encontrado"
    body = "\n\n".join(signals) if signals else "No se detectaron senales potenciales en el pre-scan. Continuar solo si aparece evidencia durante la revision manual."
    return f"""# Specialized Evidence: {title}

Este archivo registra senales potenciales. No confirma amenazas, vulnerabilidades, fallos QA,
incumplimientos ni problemas especializados sin evidencia directa.

## Estado

**Estado:** {status}
**Buscado en:** {searched}
**Efecto en la revision:** aporta senales potenciales para revision especializada, no conclusiones.
**Continuidad:** continuar con revision base y especialistas solo si la evidencia lo justifica.

## Senales potenciales

{body}

## Actualizaciones

- Fecha/hora: {timestamp}
- Cambio: pre-scan especializado registrado.
"""


def signal(prefix: str, num: int, title: str, kind: str, observed: str, evidence: str, source: str, action: str) -> str:
    return f"""### {prefix}-POT-{num:03d}: {title}

**Estado:** potencial
**Tipo:** {kind}
**Senal observada:** {observed}
**Evidencia:** {evidence}
**Fuente relacionada:** {source}
**Impacto potencial:** medio
**Confianza:** baja
**Por que requiere revision especializada:** la evidencia de pre-scan solo indica una posible zona de revision.
**No afirmar:** amenaza, explotabilidad, fallo o incumplimiento confirmado sin evidencia directa.
**Puede convertirse en deuda tecnica:** pendiente
**Accion sugerida:** {action}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository or project root.")
    parser.add_argument("--max-files", type=int, default=5000)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    governance = root / "governance"
    if not governance.is_dir():
        print(f"ERROR: missing {governance}. Run init_governance.py first.")
        return 1

    files = visible_files(root, args.max_files)
    manifests = match_any(files, MANIFEST_PATTERNS)
    locks = match_any(files, LOCK_PATTERNS)
    docker = match_any(files, DOCKER_PATTERNS)
    docs = match_any(files, DOC_PATTERNS)
    agents = match_any(files, AGENT_PATTERNS)
    tests = match_any(files, TEST_PATTERNS)
    configs = match_any(files, CONFIG_PATTERNS)
    data_files = match_any(files, DATA_PATTERNS)
    satd = satd_hits(root, files)

    git_ok, git_root = run_git(root, ["rev-parse", "--show-toplevel"])
    git_status = git_log = ""
    if git_ok:
        _, git_status = run_git(root, ["status", "--short"])
        _, git_log = run_git(root, ["log", "--oneline", "--decorate", "-n", "15"])

    code_body = f"""Manifests:
{bullet(manifests)}

Lockfiles:
{bullet(locks)}

Config/env candidates:
{bullet(configs)}

Docker/Compose candidates:
{bullet(docker)}

Tests candidates:
{bullet(tests)}

SATD signals:
{bullet(satd)}
"""
    doc_body = f"""Documentation candidates:
{bullet(docs)}
"""
    version_body = (
        f"Git repository detected at `{git_root}`.\n\nRecent status:\n```text\n{git_status or 'clean or no short status output'}\n```\n\nRecent commits:\n```text\n{git_log or 'no log output'}\n```"
        if git_ok
        else "Git repository not detected or unavailable from this root."
    )
    agents_body = f"""Agent/rule candidates:
{bullet(agents)}
"""

    outputs = {
        "evidence/code.md": source_doc(
            "code",
            "CODE",
            "revisado" if manifests or configs or tests or docker or satd else "parcial",
            "manifests, lockfiles, config, tests, Docker, SATD terms",
            "aporta punto de partida ejecutable; requiere revision manual",
            "se continua con documentacion",
            code_body,
        ),
        "evidence/documentation.md": source_doc(
            "documentation",
            "DOC",
            "revisado" if docs else "no encontrado",
            "README*, docs/, doc/, architecture/, adr/, adrs/, madr/",
            "define intencion declarada si existe",
            "se continua con versionado aunque no haya documentacion",
            doc_body,
        ),
        "evidence/versioning.md": source_doc(
            "versioning",
            "VER",
            "revisado" if git_ok else "no encontrado",
            "git rev-parse, git status --short, git log --oneline -n 15",
            "aporta evolucion si git esta disponible",
            "se continua con agentes aunque git no exista",
            version_body,
        ),
        "evidence/agents.md": source_doc(
            "agents",
            "AGT",
            "revisado" if agents else "no encontrado",
            "AGENTS.md, .agents/, .codex/, prompt/rules file names",
            "aporta reglas operativas si existen",
            "se continua con decisiones aunque no haya reglas de agente",
            agents_body,
        ),
    }

    security_signals: list[str] = []
    if locks:
        security_signals.append(
            signal(
                "SEC",
                1,
                "Lockfiles detectados sin auditoria especializada ejecutada",
                "security",
                "existen lockfiles que podrian ser insumo para revision de dependencias",
                ", ".join(f"`{item}`" for item in locks),
                "`evidence/code.md`",
                "solicitar revision especializada de seguridad o usar una skill/plugin de seguridad disponible; no corregir desde esta skill",
            )
        )
    qa_signals: list[str] = []
    if not tests:
        qa_signals.append(
            signal(
                "QA",
                1,
                "No se detectaron tests en pre-scan",
                "qa",
                "no se encontraron archivos o carpetas de test con los patrones iniciales",
                "patrones revisados: *test*, *spec*, tests/, test/, __tests__/",
                "`evidence/code.md`",
                "confirmar estructura de pruebas o revisar manualmente calidad/cobertura antes de concluir",
            )
        )
    data_signals: list[str] = []
    if data_files:
        data_signals.append(
            signal(
                "DATA",
                1,
                "Artefactos de datos detectados",
                "data",
                "existen artefactos que podrian requerir revision de modelo, migraciones o consistencia",
                ", ".join(f"`{item}`" for item in data_files[:10]),
                "`evidence/code.md`",
                "revisar modelo de datos y migraciones si el flujo evaluado depende de datos persistidos",
            )
        )

    specialized_outputs = {
        "evidence/specialized/security.md": specialized_doc(
            "security", "SEC", "security", security_signals, "lockfiles, manifests, config candidates"
        ),
        "evidence/specialized/qa.md": specialized_doc(
            "qa", "QA", "qa", qa_signals, "test/spec file patterns"
        ),
        "evidence/specialized/data.md": specialized_doc(
            "data", "DATA", "data", data_signals, "migrations, schemas, models"
        ),
        "evidence/specialized/performance.md": specialized_doc(
            "performance", "PERF", "performance", [], "pre-scan did not execute profilers or load tests"
        ),
        "evidence/specialized/compliance.md": specialized_doc(
            "compliance", "COMP", "compliance", [], "pre-scan did not evaluate compliance controls"
        ),
    }

    count_map = {
        "Security": len(security_signals),
        "QA": len(qa_signals),
        "Data": len(data_signals),
        "Performance": 0,
        "Compliance": 0,
    }
    specialized_outputs["evidence/specialized/index.md"] = "# Specialized Evidence Index\n\n## Conteos\n\n| Tipo | Archivo | Conteo | Estado |\n|---|---|---:|---|\n" + "\n".join(
        f"| {name} | `{name.lower() if name != 'QA' else 'qa'}.md` | {count} | {'parcial' if count else 'no encontrado'} |"
        for name, count in count_map.items()
    ) + "\n\n## Regla\n\nEstas entradas son potenciales y requieren evidencia directa o especialista antes de afirmar un problema confirmado.\n"

    for relative, content in {**outputs, **specialized_outputs}.items():
        path = governance / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"Updated {path.relative_to(root)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
