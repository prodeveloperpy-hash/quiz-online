from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator
from .models import QuestionType, QuizStatus, Role


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6)
    role: Role
    department: str | None = None
    semester: int | None = Field(default=None, ge=1, le=20)
    section: str | None = None


class OptionIn(BaseModel):
    text: str
    is_correct: bool = False


class QuestionIn(BaseModel):
    text: str
    question_type: QuestionType
    marks: float = Field(gt=0)
    options: list[OptionIn] = []

    @model_validator(mode="after")
    def validate_mcq(self):
        if self.question_type == QuestionType.mcq:
            if len(self.options) < 2 or sum(o.is_correct for o in self.options) != 1:
                raise ValueError("MCQ must contain at least two options and exactly one correct answer")
        return self


class QuizCreate(BaseModel):
    title: str
    description: str = ""
    department: str
    semester: int = Field(ge=1, le=20)
    section: str
    duration_minutes: int = Field(ge=1, le=240)
    starts_at: datetime
    ends_at: datetime
    questions: list[QuestionIn]


class AnswerIn(BaseModel):
    question_id: int
    selected_option_id: int | None = None
    text_answer: str | None = None


class SaveAnswersIn(BaseModel):
    answers: list[AnswerIn]


class ViolationIn(BaseModel):
    reason: str = "Browser tab/window switched"


class GradeIn(BaseModel):
    awarded_marks: float = Field(ge=0)
    feedback: str = ""


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=6)
    department: str | None = None
    semester: int | None = Field(default=None, ge=1, le=20)
    section: str | None = None
    is_active: bool | None = None


class DepartmentIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    is_active: bool = True


class SemesterIn(BaseModel):
    number: int = Field(ge=1, le=20)
    name: str = Field(min_length=1, max_length=100)
    is_active: bool = True


class SectionIn(BaseModel):
    name: str = Field(min_length=1, max_length=30)
    is_active: bool = True
