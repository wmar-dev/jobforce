# Contract: render_template.py CLI

## Invocation

```
python backend/jobforce/scripts/render_template.py <json_input_path> <tex_output_path>
```

## Arguments

| Position | Name             | Description                                               |
|----------|------------------|-----------------------------------------------------------|
| 1        | json_input_path  | Path to a JSON file containing the resume `structured_data` object |
| 2        | tex_output_path  | Path where the rendered `.tex` file will be written       |

## Behaviour

1. Reads and parses the JSON file at `json_input_path`.
2. Loads `resume.tex.j2` from the templates directory.
3. Applies the `latex_escape` Jinja2 filter to all string values before interpolation.
4. Writes the rendered LaTeX source to `tex_output_path`.
5. Exits `0` on success.

## Exit codes

| Code | Meaning                                                        |
|------|----------------------------------------------------------------|
| 0    | Success — `.tex` file written                                  |
| 1    | Error — missing args, unreadable JSON, template error, or write failure; error printed to stderr |

## latex_escape filter

Escapes the 10 LaTeX special characters in string values:

| Character | Escaped as    |
|-----------|---------------|
| `&`       | `\&`          |
| `%`       | `\%`          |
| `$`       | `\$`          |
| `#`       | `\#`          |
| `_`       | `\_`          |
| `{`       | `\{`          |
| `}`       | `\}`          |
| `~`       | `\textasciitilde{}` |
| `^`       | `\textasciicircum{}` |
| `\`       | `\textbackslash{}` |

Applied automatically via the Jinja2 filter — template authors use `\VAR{value|latex_escape}`.
