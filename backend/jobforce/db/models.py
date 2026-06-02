from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> str:
    return datetime.now(UTC).isoformat()


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    domain: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    careers_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now, onupdate=_now)

    job_listings: Mapped[list[JobListing]] = relationship(
        "JobListing", back_populates="company", cascade="all, delete-orphan"
    )
    meeting_notes: Mapped[list[MeetingNote]] = relationship(
        "MeetingNote", back_populates="company", cascade="all, delete-orphan"
    )


_VALID_STATUSES = (
    "('saved','applied','interviewing','offer','rejected','withdrawn','archived','shortlisted')"
)


class JobListing(Base):
    __tablename__ = "job_listings"
    __table_args__ = (
        CheckConstraint(
            f"status IN {_VALID_STATUSES}",
            name="ck_job_listings_status",
        ),
        Index("idx_job_listings_company", "company_id"),
        Index("idx_job_listings_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    role_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="saved")
    fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fit_scored: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fit_confidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    fit_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    crawled_at: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now, onupdate=_now)

    company: Mapped[Company] = relationship("Company", back_populates="job_listings")
    status_transitions: Mapped[list[StatusTransition]] = relationship(
        "StatusTransition", back_populates="job_listing", cascade="all, delete-orphan"
    )
    page_snapshot: Mapped[PageSnapshot | None] = relationship(
        "PageSnapshot", back_populates="job_listing", uselist=False, cascade="all, delete-orphan"
    )
    resumes: Mapped[list[Resume]] = relationship(
        "Resume", back_populates="job_listing", cascade="all, delete-orphan"
    )
    interview_sessions: Mapped[list[InterviewSession]] = relationship(
        "InterviewSession", back_populates="job_listing", cascade="all, delete-orphan"
    )
    meeting_notes: Mapped[list[MeetingNote]] = relationship(
        "MeetingNote", back_populates="job_listing"
    )


class StatusTransition(Base):
    __tablename__ = "status_transitions"
    __table_args__ = (Index("idx_status_transitions_job", "job_listing_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_listing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_listings.id"), nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    to_status: Mapped[str] = mapped_column(Text, nullable=False)
    transitioned_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now)

    job_listing: Mapped[JobListing] = relationship(
        "JobListing", back_populates="status_transitions"
    )


class PageSnapshot(Base):
    __tablename__ = "page_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_listing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_listings.id"), nullable=False, unique=True
    )
    html_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    captured_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now)

    job_listing: Mapped[JobListing] = relationship("JobListing", back_populates="page_snapshot")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    is_base: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    job_listing_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("job_listings.id"), nullable=True
    )
    structured_data: Mapped[str] = mapped_column(Text, nullable=False)
    latex_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now, onupdate=_now)

    job_listing: Mapped[JobListing | None] = relationship("JobListing", back_populates="resumes")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    __table_args__ = (
        CheckConstraint("session_type IN ('prep','mock')", name="ck_interview_session_type"),
        Index("idx_interview_sessions_job", "job_listing_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_listing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_listings.id"), nullable=False
    )
    session_type: Mapped[str] = mapped_column(Text, nullable=False, default="prep")
    questions: Mapped[str] = mapped_column(Text, nullable=False)
    overall_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now, onupdate=_now)

    job_listing: Mapped[JobListing] = relationship(
        "JobListing", back_populates="interview_sessions"
    )


class MeetingNote(Base):
    __tablename__ = "meeting_notes"
    __table_args__ = (
        Index("idx_meeting_notes_company", "company_id"),
        Index("idx_meeting_notes_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    job_listing_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("job_listings.id"), nullable=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now, onupdate=_now)

    company: Mapped[Company] = relationship("Company", back_populates="meeting_notes")
    job_listing: Mapped[JobListing | None] = relationship(
        "JobListing", back_populates="meeting_notes"
    )


class SearchConfigRecord(Base):
    __tablename__ = "search_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
