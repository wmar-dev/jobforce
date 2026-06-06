"""CLI script: render resume.tex.j2 template to a .tex file.

Usage:
    python render_template.py <json_input_path> <tex_output_path>

Exits 0 on success, 1 on any error (printed to stderr).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

_LATEX_SPECIAL = [
    ("\\", r"\textbackslash{}"),  # must be first to avoid double-escaping
    ("&", r"\&"),
    ("%", r"\%"),
    ("$", r"\$"),
    ("#", r"\#"),
    ("_", r"\_"),
    ("{", r"\{"),
    ("}", r"\}"),
    ("~", r"\textasciitilde{}"),
    ("^", r"\textasciicircum{}"),
]


def latex_escape(value: str) -> str:
    """Escape the 10 LaTeX special characters in a string value."""
    # Escape backslash first, then the rest
    result = value.replace("\\", r"\textbackslash{}")
    for char, escaped in _LATEX_SPECIAL[1:]:
        result = result.replace(char, escaped)
    return result


def _build_env() -> Environment:
    env = Environment(
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
    env.filters["latex_escape"] = latex_escape
    return env


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} <json_input_path> <tex_output_path>",
            file=sys.stderr,
        )
        return 1

    json_path = Path(sys.argv[1])
    tex_path = Path(sys.argv[2])

    try:
        structured_data = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error reading JSON input: {exc}", file=sys.stderr)
        return 1

    try:
        env = _build_env()
        template = env.get_template("resume.tex.j2")
        tex_source = template.render(data=structured_data)
    except Exception as exc:
        print(f"Template rendering error: {exc}", file=sys.stderr)
        return 1

    try:
        tex_path.parent.mkdir(parents=True, exist_ok=True)
        tex_path.write_text(tex_source, encoding="utf-8")
    except OSError as exc:
        print(f"Error writing .tex file: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
