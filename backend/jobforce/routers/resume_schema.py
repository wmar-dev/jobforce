"""Documentation-only shapes: the resume's structured data and enum-like string fields.

These types make the OpenAPI document (and the frontend types generated from it)
describe real payloads *without* adding runtime validation. The API has always
accepted any resume JSON and any string in these fields; tightening that would
reject data the skills and extension send today, so validation is skipped.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, WithJsonSchema

from jobforce.services.scout import _VALID_TRANSITIONS

_PERMISSIVE = ConfigDict(extra="allow")


class PersonalInfo(BaseModel):
    """Contact details shown in the resume header."""

    model_config = _PERMISSIVE
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    website: str | None = None


class WorkHistoryItem(BaseModel):
    """One role; dates are free-form strings such as "2021-03"."""

    model_config = _PERMISSIVE
    company: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None
    bullets: list[str] | None = None


class EducationItem(BaseModel):
    """One degree or program."""

    model_config = _PERMISSIVE
    degree: str | None = None
    institution: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    gpa: str | None = None
    notes: str | None = None


class ProjectItem(BaseModel):
    """A side or portfolio project."""

    model_config = _PERMISSIVE
    name: str | None = None
    description: str | None = None
    url: str | None = None
    bullets: list[str] | None = None


class CertificationItem(BaseModel):
    """A professional certification."""

    model_config = _PERMISSIVE
    name: str | None = None
    issuer: str | None = None
    year: int | None = None


class Coursework(BaseModel):
    """Courses completed with a single provider."""

    model_config = _PERMISSIVE
    provider: str | None = None
    courses: list[str] | None = None


class PatentItem(BaseModel):
    """A granted or filed patent."""

    model_config = _PERMISSIVE
    title: str | None = None
    number: str | None = None


class ResumeStructuredData(BaseModel):
    """Resume content. Every key is optional and extra keys are kept; not validated."""

    model_config = _PERMISSIVE
    personal_info: PersonalInfo | None = None
    summary: str | None = None
    skills: list[str] | None = None
    work_history: list[WorkHistoryItem] | None = None
    education: list[EducationItem] | None = None
    projects: list[ProjectItem] | None = None
    certifications: list[CertificationItem] | None = None
    coursework: Coursework | None = None
    patents: list[PatentItem] | None = None


_RESUME_REF = "#/components/schemas/ResumeStructuredData"

# Runtime type stays Any so odd payloads round-trip untouched and never trigger
# serializer warnings (SkipValidation[Model] warns on non-conforming dicts); the
# schema points at the component that add_resume_components() registers.
# allOf wrapper: a bare top-level $ref makes pydantic try to resolve it locally.
PermissiveResumeData = Annotated[Any, WithJsonSchema({"allOf": [{"$ref": _RESUME_REF}]})]


def add_resume_components(openapi: dict[str, Any]) -> dict[str, Any]:
    """Register ResumeStructuredData and its nested models as OpenAPI components."""
    schema = ResumeStructuredData.model_json_schema(ref_template="#/components/schemas/{model}")
    components = openapi.setdefault("components", {}).setdefault("schemas", {})
    for name, definition in schema.pop("$defs", {}).items():
        components.setdefault(name, definition)
    components.setdefault("ResumeStructuredData", schema)
    return openapi


PIPELINE_STATUSES: tuple[str, ...] = tuple(_VALID_TRANSITIONS)
ROLE_TYPES: tuple[str, ...] = ("full-time", "part-time", "contract", "internship", "other")
FIT_CONFIDENCES: tuple[str, ...] = ("high", "medium", "low")
QUESTION_CATEGORIES: tuple[str, ...] = ("behavioral", "coding", "system_design", "role_specific")


def _enum(values: tuple[str, ...]) -> dict[str, Any]:
    return {"type": "string", "enum": list(values)}


def _nullable_enum(values: tuple[str, ...]) -> dict[str, Any]:
    return {"anyOf": [_enum(values), {"type": "null"}]}


PipelineStatusStr = Annotated[str, WithJsonSchema(_enum(PIPELINE_STATUSES))]
OptionalPipelineStatusStr = Annotated[str | None, WithJsonSchema(_nullable_enum(PIPELINE_STATUSES))]
OptionalRoleTypeStr = Annotated[str | None, WithJsonSchema(_nullable_enum(ROLE_TYPES))]
FitConfidenceStr = Annotated[str, WithJsonSchema(_enum(FIT_CONFIDENCES))]
OptionalFitConfidenceStr = Annotated[str | None, WithJsonSchema(_nullable_enum(FIT_CONFIDENCES))]
QuestionCategoryStr = Annotated[str, WithJsonSchema(_enum(QUESTION_CATEGORIES))]
