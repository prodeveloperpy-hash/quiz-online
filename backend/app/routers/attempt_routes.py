import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..auth import allow_roles
from ..database import get_db
from ..email_service import send_result_email
from ..models import Answer, Attempt, AttemptStatus, Question, QuestionType, Quiz, QuizStatus, Role, User
from ..schemas import AttemptOut, GradeIn, SaveAnswersIn

router = APIRouter(prefix="/attempts", tags=["Attempts"])


def load_attempt(db: Session, attempt_id: int) -> Attempt | None:
    return db.scalar(select(Attempt).where(Attempt.id == attempt_id).options(
        selectinload(Attempt.answers).selectinload(Answer.question).selectinload(Question.options),
        selectinload(Attempt.quiz).selectinload(Quiz.questions), selectinload(Attempt.student)))


def attempt_out(attempt: Attempt) -> AttemptOut:
    total = sum(question.marks for question in attempt.quiz.questions)
    return AttemptOut(id=attempt.id, quiz_id=attempt.quiz_id, student_id=attempt.student_id,
        status=attempt.status, started_at=attempt.started_at, submitted_at=attempt.submitted_at,
        objective_score=attempt.objective_score, manual_score=attempt.manual_score,
        tab_switches=attempt.tab_switches, total_marks=total,
        final_score=attempt.objective_score + attempt.manual_score)


@router.post("/quizzes/{quiz_id}/start", response_model=AttemptOut)
def start(quiz_id: int, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.student))):
    quiz = db.get(Quiz, quiz_id)
    if not quiz or quiz.status != QuizStatus.published:
        raise HTTPException(404, "Published quiz not found")
    if quiz.department != user.department or quiz.semester != user.semester:
        raise HTTPException(403, "Quiz is not assigned to you")
    existing = db.scalar(select(Attempt).where(Attempt.quiz_id == quiz_id, Attempt.student_id == user.id))
    if existing:
        attempt = load_attempt(db, existing.id)
        return attempt_out(attempt)
    attempt = Attempt(quiz_id=quiz_id, student_id=user.id)
    db.add(attempt)
    db.commit()
    return attempt_out(load_attempt(db, attempt.id))


def ensure_active(attempt: Attempt, user: User):
    if attempt.student_id != user.id:
        raise HTTPException(403, "This attempt belongs to another student")
    if attempt.status != AttemptStatus.in_progress:
        raise HTTPException(409, "Attempt has already been submitted")


def upsert_answers(db: Session, attempt: Attempt, payload: SaveAnswersIn):
    question_map = {q.id: q for q in attempt.quiz.questions}
    for item in payload.answers:
        if item.question_id not in question_map:
            raise HTTPException(400, "Answer contains a question outside this quiz")
        answer = db.scalar(select(Answer).where(Answer.attempt_id == attempt.id, Answer.question_id == item.question_id))
        if not answer:
            answer = Answer(attempt_id=attempt.id, question_id=item.question_id)
            db.add(answer)
        answer.selected_option_ids = json.dumps(sorted(set(item.selected_option_ids)))
        answer.text_answer = item.text_answer.strip()


@router.put("/{attempt_id}/answers", response_model=AttemptOut)
def save_answers(attempt_id: int, payload: SaveAnswersIn, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.student))):
    attempt = load_attempt(db, attempt_id)
    if not attempt:
        raise HTTPException(404, "Attempt not found")
    ensure_active(attempt, user)
    if datetime.utcnow() > attempt.started_at + timedelta(minutes=attempt.quiz.duration_minutes):
        return submit(attempt_id, payload, db, user)
    upsert_answers(db, attempt, payload)
    db.commit()
    return attempt_out(load_attempt(db, attempt_id))


@router.post("/{attempt_id}/submit", response_model=AttemptOut)
def submit(attempt_id: int, payload: SaveAnswersIn, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.student))):
    attempt = load_attempt(db, attempt_id)
    if not attempt:
        raise HTTPException(404, "Attempt not found")
    ensure_active(attempt, user)
    upsert_answers(db, attempt, payload)
    db.flush()
    attempt = load_attempt(db, attempt_id)
    objective_score = 0.0
    has_short = False
    for answer in attempt.answers:
        question = answer.question
        if question.question_type == QuestionType.short:
            has_short = True
            answer.is_correct = None
            answer.awarded_marks = None
            continue
        selected = set(json.loads(answer.selected_option_ids or "[]"))
        correct = {option.id for option in question.options if option.is_correct}
        answer.is_correct = selected == correct
        answer.awarded_marks = question.marks if answer.is_correct else 0
        objective_score += answer.awarded_marks
    attempt.objective_score = objective_score
    attempt.submitted_at = datetime.utcnow()
    attempt.status = AttemptStatus.awaiting_review if has_short else AttemptStatus.graded
    db.commit()
    if attempt.status == AttemptStatus.graded:
        _email_final_result(db, load_attempt(db, attempt_id))
    return attempt_out(load_attempt(db, attempt_id))


@router.post("/{attempt_id}/tab-switch", response_model=AttemptOut)
def tab_switch(attempt_id: int, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.student))):
    attempt = load_attempt(db, attempt_id)
    if not attempt:
        raise HTTPException(404, "Attempt not found")
    ensure_active(attempt, user)
    attempt.tab_switches += 1
    db.commit()
    return attempt_out(load_attempt(db, attempt_id))


@router.get("/review/pending")
def pending_reviews(db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin, Role.teacher))):
    query = select(Attempt).where(Attempt.status == AttemptStatus.awaiting_review).options(
        selectinload(Attempt.student), selectinload(Attempt.quiz),
        selectinload(Attempt.answers).selectinload(Answer.question))
    attempts = list(db.scalars(query).unique())
    if user.role == Role.teacher:
        attempts = [a for a in attempts if a.quiz.creator_id == user.id]
    return [{"id": a.id, "student": a.student.name, "quiz": a.quiz.title,
             "answers": [{"answer_id": ans.id, "question": ans.question.text,
                          "answer": ans.text_answer, "max_marks": ans.question.marks,
                          "awarded_marks": ans.awarded_marks, "feedback": ans.feedback}
                         for ans in a.answers if ans.question.question_type == QuestionType.short]}
            for a in attempts]


@router.patch("/answers/{answer_id}/grade")
def grade_answer(answer_id: int, payload: GradeIn, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin, Role.teacher))):
    answer = db.scalar(select(Answer).where(Answer.id == answer_id).options(
        selectinload(Answer.question), selectinload(Answer.attempt).selectinload(Attempt.quiz)))
    if not answer or answer.question.question_type != QuestionType.short:
        raise HTTPException(404, "Short answer not found")
    if user.role == Role.teacher and answer.attempt.quiz.creator_id != user.id:
        raise HTTPException(403, "This quiz belongs to another teacher")
    if payload.awarded_marks > answer.question.marks:
        raise HTTPException(400, "Awarded marks cannot exceed question marks")
    answer.awarded_marks = payload.awarded_marks
    answer.is_correct = payload.awarded_marks == answer.question.marks
    answer.feedback = payload.feedback
    db.flush()
    attempt = load_attempt(db, answer.attempt_id)
    short_answers = [a for a in attempt.answers if a.question.question_type == QuestionType.short]
    if short_answers and all(a.awarded_marks is not None for a in short_answers):
        attempt.manual_score = sum(a.awarded_marks or 0 for a in short_answers)
        attempt.status = AttemptStatus.graded
        db.commit()
        _email_final_result(db, load_attempt(db, attempt.id))
    else:
        db.commit()
    return {"message": "Marks saved"}


def _email_final_result(db: Session, attempt: Attempt):
    if attempt.result_emailed:
        return
    total = sum(q.marks for q in attempt.quiz.questions)
    send_result_email(attempt.student.email, attempt.student.name, attempt.quiz.title,
                      attempt.objective_score + attempt.manual_score, total)
    attempt.result_emailed = True
    db.commit()


@router.get("/{attempt_id}", response_model=AttemptOut)
def get_attempt(attempt_id: int, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.student))):
    attempt = load_attempt(db, attempt_id)
    if not attempt or attempt.student_id != user.id:
        raise HTTPException(404, "Attempt not found")
    return attempt_out(attempt)

