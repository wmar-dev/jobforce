"""Forge service — resume diff computation and PDF rendering via LaTeX.

AI tailoring is performed by Claude Code via the /forge-tailor skill.
This module retains compute_diff and render_pdf for use by the router.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        variable_start_string=r"\VAR{",
        variable_end_string="}",
        block_start_string=r"\BLOCK{",
        block_end_string="}",
        comment_start_string=r"\#{",
        comment_end_string="}",
        trim_blocks=True,
        autoescape=False,
    )


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


async def render_pdf(structured_data: dict[str, Any]) -> bytes:
    """Render structured_data to PDF via LaTeX. Raises RuntimeError if LaTeX unavailable."""
    if not shutil.which("latexmk") and not shutil.which("pdflatex"):
        raise RuntimeError("LaTeX not available — install texlive to generate PDFs")

    env = _get_jinja_env()
    template = env.get_template("resume.tex.j2")
    tex_source = template.render(data=structured_data)

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = Path(tmpdir) / "resume.tex"
        tex_path.write_text(tex_source, encoding="utf-8")

        cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", "-quiet", str(tex_path)]
        if shutil.which("latexmk") is None:
            cmd = ["pdflatex", "-interaction=nonstopmode", str(tex_path)]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=tmpdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=25)
        except TimeoutError as exc:
            raise RuntimeError("LaTeX rendering timed out") from exc
        except Exception as exc:
            raise RuntimeError(f"LaTeX subprocess error: {exc}") from exc

        if proc.returncode != 0:
            raise RuntimeError(
                f"LaTeX compilation failed (exit {proc.returncode}): {stderr.decode()[:500]}"
            )

        pdf_path = Path(tmpdir) / "resume.pdf"
        if not pdf_path.exists():
            raise RuntimeError("PDF file was not produced by LaTeX")

        return pdf_path.read_bytes()
