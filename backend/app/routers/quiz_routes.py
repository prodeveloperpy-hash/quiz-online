from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..auth import allow_roles, current_user
from ..database import get_db
from ..models import Option, Question, QuestionType, Quiz, QuizStatus, Role, User
from ..schemas import QuizCreate, QuizOut

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


def load_quiz(db: Session, quiz_id: int) -> Quiz | None:
    return db.scalar(select(Quiz).where(Quiz.id == quiz_id).options(selectinload(Quiz.questions).selectinload(Question.options)))


@router.post("", response_model=QuizOut)
def create_quiz(data: QuizCreate, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin, Role.teacher))):
    if not data.questions:
        raise HTTPException(400, "At least one question is required")
    quiz = Quiz(title=data.title, description=data.description, department=data.department,
                semester=data.semester, duration_minutes=data.duration_minutes, creator_id=user.id)
    db.add(quiz)
    db.flush()
    for index, item in enumerate(data.questions):
        if item.question_type in (QuestionType.mcq, QuestionType.msq):
            correct_count = sum(option.is_correct for option in item.options)
            if not item.options or correct_count == 0:
                raise HTTPException(400, f"Objective question {index + 1} needs options and a correct answer")
            if item.question_type == QuestionType.mcq and correct_count != 1:
                raise HTTPException(400, f"MCQ {index + 1} must have exactly one correct option")
        question = Question(quiz_id=quiz.id, text=item.text, question_type=item.question_type,
                            marks=item.marks, order_index=index)
        db.add(question)
        db.flush()
        db.add_all([Option(question_id=question.id, text=o.text, is_correct=o.is_correct) for o in item.options])
    db.commit()
    return load_quiz(db, quiz.id)


@router.get("", response_model=list[QuizOut])
def list_quizzes(db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = select(Quiz).options(selectinload(Quiz.questions).selectinload(Question.options)).order_by(Quiz.created_at.desc())
    if user.role == Role.student:
        query = query.where(Quiz.status == QuizStatus.published, Quiz.department == user.department, Quiz.semester == user.semester)
    elif user.role == Role.teacher:
        query = query.where(Quiz.creator_id == user.id)
    return list(db.scalars(query).unique())


@router.get("/{quiz_id}", response_model=QuizOut)
def get_quiz(quiz_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    quiz = load_quiz(db, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    if user.role == Role.student and (quiz.status != QuizStatus.published or quiz.department != user.department or quiz.semester != user.semester):
        raise HTTPException(403, "This quiz is not assigned to your department and semester")
    if user.role == Role.teacher and quiz.creator_id != user.id:
        raise HTTPException(403, "This quiz belongs to another teacher")
    return quiz


@router.patch("/{quiz_id}/publish", response_model=QuizOut)
def publish_quiz(quiz_id: int, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin, Role.teacher))):
    quiz = load_quiz(db, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    if user.role == Role.teacher and quiz.creator_id != user.id:
        raise HTTPException(403, "This quiz belongs to another teacher")
    quiz.status = QuizStatus.published
    db.commit()
    return load_quiz(db, quiz_id)

