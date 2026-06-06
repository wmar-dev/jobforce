"""Forge service — resume diff computation and CLI-based LaTeX/PDF export.

AI tailoring is performed by Claude Code via the /forge-tailor skill.
Template rendering (.tex.j2 → .tex) and PDF compilation (.tex → .pdf) are
both performed by invoking CLI tools as subprocesses — no in-process Jinja2
or LaTeX library calls on the export path.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
_OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "output"


def _slugify(value: str) -> str:
    """Lowercase, replace non-alphanumeric runs with '-', strip leading/trailing '-'."""
    lowered = value.lower()
    slugged = re.sub(r"[^a-z0-9]+", "-", lowered)
    return slugged.strip("-")


def _build_filename_stem(company: str, title: str) -> str:
    """Build a unique filename stem: resume-<company>-<title>-<YYYYMMDD-HHMMSS>."""
    company_slug = _slugify(company)
    title_slug = _slugify(title)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    parts = ["resume"]
    if company_slug:
        parts.append(company_slug)
    if title_slug:
        parts.append(title_slug)
    parts.append(timestamp)
    return "-".join(parts)


def compute_diff(original: dict[str, Any], tailored: dict[str, Any]) -> list[dict[str, Any]]:
    """Return field-level diff between original and tailored structured_data."""
    diffs: list[dict[str, Any]] = []

    def _compare(key: str, orig: Any, tail: Any) -> None:
        orig_str = json.dumps(orig, ensure_ascii=False)
        tail_str = json.dumps(tail, ensure_ascii=False)
        if orig_str != tail_str:
            diffs.append({"field": key, "original": orig_str, "tailored": tail_str})

    all_keys = set(original.keys()) | set(tailored.keys())
    for key in sorted(all_keys):
        if key in original and key in tailored:
            _compare(key, original[key], tailored[key])
        elif key in tailored:
            diffs.append({"field": key, "original": "", "tailored": json.dumps(tailored[key])})
        else:
            diffs.append({"field": key, "original": json.dumps(original[key]), "tailored": ""})

    return diffs


async def render_tex_cli(
    structured_data: dict[str, Any],
    output_dir: Path,
    filename_stem: str,
) -> Path:
    """Invoke render_template.py as a subprocess to produce a .tex file.

    Raises RuntimeError on failure.
    """
    script = _SCRIPTS_DIR / "render_template.py"
    if not script.exists():
        raise RuntimeError(f"render_template.py not found at {script}")

    output_dir.mkdir(parents=True, exist_ok=True)
    tex_path = output_dir / f"{filename_stem}.tex"

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        json.dump(structured_data, tmp, ensure_ascii=False)
        tmp_path = Path(tmp.name)

    logger.info("render_tex_cli: rendering %s", tex_path)
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script),
            str(tmp_path),
            str(tex_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
    except TimeoutError as exc:
        raise RuntimeError("render_template.py timed out") from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    if proc.returncode != 0:
        raise RuntimeError(
            f"render_template.py failed (exit {proc.returncode}): {stderr.decode()[:500]}"
        )

    logger.info("render_tex_cli: wrote %s", tex_path)
    return tex_path


async def compile_pdf_cli(tex_path: Path) -> Path | None:
    """Invoke latexmk or pdflatex to compile tex_path to PDF.

    Returns the PDF path on success, None if LaTeX is not installed.
    Raises RuntimeError on compilation failure.
    """
    if not shutil.which("latexmk") and not shutil.which("pdflatex"):
        logger.warning("compile_pdf_cli: LaTeX not available — skipping PDF compilation")
        return None

    pdf_path = tex_path.with_suffix(".pdf")
    if shutil.which("latexmk"):
        cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", "-quiet", str(tex_path)]
    else:
        cmd = ["pdflatex", "-interaction=nonstopmode", str(tex_path)]

    logger.info("compile_pdf_cli: compiling %s", tex_path)
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(tex_path.parent),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=25)
    except TimeoutError as exc:
        raise RuntimeError("LaTeX compilation timed out") from exc

    if proc.returncode != 0:
        raise RuntimeError(
            f"LaTeX compilation failed (exit {proc.returncode}): {stderr.decode()[:500]}"
        )

    if not pdf_path.exists():
        raise RuntimeError("PDF file was not produced by LaTeX")

    logger.info("compile_pdf_cli: wrote %s", pdf_path)
    return pdf_path


class ExportResult:
    __slots__ = ("tex_path", "pdf_path")

    def __init__(self, tex_path: str, pdf_path: str | None) -> None:
        self.tex_path = tex_path
        self.pdf_path = pdf_path


async def export_resume(
    resume: Any,
    job_company: str = "unknown",
    job_title: str = "resume",
) -> ExportResult:
    """Render a resume to .tex and PDF, write both to output/, return their paths.

    ExportResult.pdf_path is None when LaTeX is unavailable — not an error condition.
    """
    structured_data: dict[str, Any] = json.loads(resume.structured_data)
    filename_stem = _build_filename_stem(job_company, job_title)

    output_dir = _OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    tex_path = await render_tex_cli(structured_data, output_dir, filename_stem)
    pdf_path = await compile_pdf_cli(tex_path)

    return ExportResult(
        tex_path=str(tex_path),
        pdf_path=str(pdf_path) if pdf_path else None,
    )
