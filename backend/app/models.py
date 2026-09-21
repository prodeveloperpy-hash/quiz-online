from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Role(str, Enum):
    admin = "admin"
    teacher = "teacher"
    student = "student"


class QuestionType(str, Enum):
    mcq = "mcq"
    short = "short"


class QuizStatus(str, Enum):
    draft = "draft"
    published = "published"
    closed = "closed"


class AttemptStatus(str, Enum):
    in_progress = "in_progress"
    pending_review = "pending_review"
    completed = "completed"
    auto_submitted = "auto_submitted"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(SAEnum(Role))
    roll_number: Mapped[str | None] = mapped_column(String(50), unique=True, index=True, nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    semester: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Quiz(Base):
    __tablename__ = "quizzes"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text, default="")
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    department: Mapped[str] = mapped_column(String(100))
    semester: Mapped[int] = mapped_column(Integer)
    section: Mapped[str] = mapped_column(String(20))
    audiences: Mapped[list | None] = mapped_column(JSON, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[QuizStatus] = mapped_column(SAEnum(QuizStatus), default=QuizStatus.draft)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    creator: Mapped[User] = relationship()
    questions: Mapped[list["Question"]] = relationship(back_populates="quiz", cascade="all, delete-orphan", order_by="Question.position")


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"))
    text: Mapped[str] = mapped_column(Text)
    question_type: Mapped[QuestionType] = mapped_column(SAEnum(QuestionType))
    marks: Mapped[float] = mapped_column(Float, default=1)
    position: Mapped[int] = mapped_column(Integer, default=0)
    quiz: Mapped[Quiz] = relationship(back_populates="questions")
    options: Mapped[list["Option"]] = relationship(back_populates="question", cascade="all, delete-orphan")


class Option(Base):
    __tablename__ = "options"
    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    text: Mapped[str] = mapped_column(String(500))
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    question: Mapped[Question] = relationship(back_populates="options")


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (UniqueConstraint("quiz_id", "student_id", "attempt_number"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[AttemptStatus] = mapped_column(SAEnum(AttemptStatus), default=AttemptStatus.in_progress)
    objective_score: Mapped[float] = mapped_column(Float, default=0)
    manual_score: Mapped[float] = mapped_column(Float, default=0)
    total_score: Mapped[float] = mapped_column(Float, default=0)
    tab_violations: Mapped[int] = mapped_column(Integer, default=0)
    submission_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    final_email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    retake_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    quiz: Mapped[Quiz] = relationship()
    student: Mapped[User] = relationship()
    answers: Mapped[list["Answer"]] = relationship(back_populates="attempt", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"
    __table_args__ = (UniqueConstraint("attempt_id", "question_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    selected_option_id: Mapped[int | None] = mapped_column(ForeignKey("options.id"), nullable=True)
    text_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    awarded_marks: Mapped[float | None] = mapped_column(Float, nullable=True)
    teacher_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt: Mapped[Attempt] = relationship(back_populates="answers")
    question: Mapped[Question] = relationship()
    selected_option: Mapped[Option | None] = relationship()


class AcademicDepartment(Base):
    __tablename__ = "academic_departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AcademicSemester(Base):
    __tablename__ = "academic_semesters"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AcademicSection(Base):
    __tablename__ = "academic_sections"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    actor_name: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity_type: Mapped[str] = mapped_column(String(50), default="quiz")
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
