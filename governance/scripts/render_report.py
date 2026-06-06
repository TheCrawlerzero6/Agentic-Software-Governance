#!/usr/bin/env python3
"""Render governance/reports/governance-report.md to a simple generated PDF."""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path


def read_config(governance: Path) -> tuple[str, str]:
    config = (governance / "governance-config.md").read_text(encoding="utf-8")
    audience_match = re.search(r"## Audiencia\s*\n\s*-\s*([a-zA-Z_-]+)", config, re.IGNORECASE)
    depth_match = re.search(r"## Profundidad\s*\n\s*-\s*([a-zA-Z_-]+)", config, re.IGNORECASE)
    audience = audience_match.group(1).lower() if audience_match else "tecnico"
    depth = depth_match.group(1).lower() if depth_match else "normal"
    return audience, depth


def markdown_to_lines(markdown: str, max_chars: int = 96) -> list[str]:
    lines: list[str] = []
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            lines.append("")
            continue
        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"`([^`]+)`", r"\1", line)
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        while len(line) > max_chars:
            split_at = line.rfind(" ", 0, max_chars)
            if split_at <= 20:
                split_at = max_chars
            lines.append(line[:split_at].rstrip())
            line = line[split_at:].strip()
        lines.append(line)
    return lines


def pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(lines: list[str], title: str) -> bytes:
    page_width = 595
    page_height = 842
    left = 48
    top = 790
    line_height = 14
    max_lines = 52
    pages = [lines[i : i + max_lines] for i in range(0, len(lines), max_lines)] or [[]]

    objects: list[bytes] = []
    pages_object_numbers: list[int] = []
    content_object_numbers: list[int] = []

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for page_lines in pages:
        content_lines = ["BT", f"/F1 10 Tf", f"{left} {top} Td"]
        content_lines.append(f"({pdf_escape(title)}) Tj")
        content_lines.append(f"0 -{line_height * 2} Td")
        for line in page_lines:
            content_lines.append(f"({pdf_escape(line)}) Tj")
            content_lines.append(f"0 -{line_height} Td")
        content_lines.append("ET")
        stream = "\n".join(content_lines).encode("utf-8")
        content_object_numbers.append(len(objects) + 1)
        objects.append(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")
        pages_object_numbers.append(len(objects) + 1)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_object_numbers[-1]} 0 R >>".encode("ascii")
        )

    kids = " ".join(f"{num} 0 R" for num in pages_object_numbers)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(pages_object_numbers)} >>".encode("ascii")

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref_pos = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository or project root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    governance = root / "governance"
    report = governance / "reports/governance-report.md"
    if not report.exists():
        print(f"ERROR: missing {report}")
        return 1

    audience, depth = read_config(governance)
    date = datetime.now().strftime("%Y%m%d")
    output_dir = governance / "reports" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"governance-report-{audience}-{date}.pdf"
    markdown = report.read_text(encoding="utf-8")
    lines = markdown_to_lines(markdown)
    title = f"Governance Report - {audience} - {depth}"
    output.write_bytes(build_pdf(lines, title))
    print(f"PDF written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
