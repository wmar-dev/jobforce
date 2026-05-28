"""Forge service — tailor resumes and render PDFs using Claude + LaTeX."""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any

import anthropic
from anthropic.types import TextBlock
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import JobListing, Resume

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


async def _call_claude(prompt: str) -> str:
    client = anthropic.AsyncAnthropic()
    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    for block in message.content:
        if isinstance(block, TextBlock):
            return block.text
    return "{}"


async def tailor_resume(
    session: AsyncSession,
    resume_id: int,
    job_id: int,
) -> dict[str, Any]:
    """Tailor a resume to a job listing. Returns {structured_data, diff}."""
    resume = await session.get(Resume, resume_id)
    if resume is None:
        raise ValueError(f"Resume {resume_id} not found")

    job = await session.get(JobListing, job_id)
    if job is None:
        raise ValueError(f"Job listing {job_id} not found")

    base_data: dict[str, Any] = json.loads(resume.structured_data)
    description = (job.description or "").strip() or f"{job.title} role"

    prompt = _build_tailor_prompt(base_data, job.title, description)

    try:
        raw = await _call_claude(prompt)
        parsed = _parse_tailor_response(raw, base_data)
    except Exception as exc:
        logger.warning("Forge tailoring failed: %s", exc)
        parsed = {"structured_data": base_data}

    tailored_data = parsed.get("structured_data", base_data)
    diff = compute_diff(base_data, tailored_data)

    return {"structured_data": tailored_data, "diff": diff}


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


def _build_tailor_prompt(base_data: dict[str, Any], job_title: str, description: str) -> str:
    return f"""You are Forge, a resume tailoring agent. Adjust the resume to better match the job description.

## Rules
1. ONLY adjust emphasis, keywords, and bullet phrasing
2. Do NOT add work history entries that don't exist
3. Do NOT fabricate companies, dates, or degrees
4. Keep all factual information accurate

## Job
Title: {job_title}
Description: {description}

## Current Resume
{json.dumps(base_data, indent=2)}

## Instructions
Return a JSON object with one key "structured_data" containing the adjusted resume.
Respond ONLY with valid JSON, no additional text."""


def _parse_tailor_response(raw: str, fallback: dict[str, Any]) -> dict[str, Any]:
    raw = raw.strip()
    if "```" in raw:
        lines = raw.split("\n")
        raw = "\n".join(line for line in lines if line.strip() not in ("```json", "```", ""))
    try:
        result: dict[str, Any] = json.loads(raw)
        return result
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse Forge response, using original")
        return {"structured_data": fallback}
