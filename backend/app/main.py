from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from .auth import allow_roles, create_token, current_user, hash_password, verify_password
from .config import settings
from .database import Base, engine, get_db
from .email_service import send_result_email
from .models import AcademicDepartment, AcademicSection, AcademicSemester, Answer, Attempt, AttemptStatus, Option, Question, QuestionType, Quiz, QuizStatus, Role, User
from .schemas import DepartmentIn, GradeIn, LoginIn, QuizCreate, SaveAnswersIn, SectionIn, SemesterIn, TokenOut, UserCreate, UserUpdate, ViolationIn


app = FastAPI(title="Quiz Online API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list({settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"}),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


def public_user(user: User) -> dict:
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role.value,
            "department": user.department,
            "semester": user.semester, "section": user.section, "is_active": user.is_active}


def quiz_dict(quiz: Quiz, include_answers: bool = False) -> dict:
    return {
        "id": quiz.id, "title": quiz.title, "description": quiz.description,
        "department": quiz.department, "semester": quiz.semester, "section": quiz.section,
        "duration_minutes": quiz.duration_minutes, "starts_at": quiz.starts_at, "ends_at": quiz.ends_at,
        "status": quiz.status.value, "creator_name": quiz.creator.name,
        "questions": [{
            "id": q.id, "text": q.text, "question_type": q.question_type.value, "marks": q.marks,
            "options": [{"id": o.id, "text": o.text, **({"is_correct": o.is_correct} if include_answers else {})} for o in q.options]
        } for q in quiz.questions]
    }


def ensure_quiz_owner(quiz: Quiz, user: User):
    if user.role == Role.teacher and quiz.creator_id != user.id:
        raise HTTPException(403, "Teachers can only manage their own quizzes")


def get_attempt(db: Session, attempt_id: int, load: bool = True) -> Attempt:
    query = select(Attempt).where(Attempt.id == attempt_id)
    if load:
        query = query.options(selectinload(Attempt.quiz).selectinload(Quiz.questions).selectinload(Question.options),
                              selectinload(Attempt.answers), selectinload(Attempt.student))
    attempt = db.scalar(query)
    if not attempt:
        raise HTTPException(404, "Attempt not found")
    return attempt


def submit_attempt(db: Session, attempt: Attempt, reason: str | None = None):
    if attempt.status != AttemptStatus.in_progress:
        return
    answer_by_question = {a.question_id: a for a in attempt.answers}
    objective = 0.0
    has_short = False
    for question in attempt.quiz.questions:
        answer = answer_by_question.get(question.id)
        if question.question_type == QuestionType.short:
            has_short = True
            continue
        if answer and answer.selected_option_id:
            correct = next((o for o in question.options if o.id == answer.selected_option_id), None)
            answer.is_correct = bool(correct and correct.is_correct)
            answer.awarded_marks = question.marks if answer.is_correct else 0
            objective += answer.awarded_marks
    attempt.objective_score = objective
    attempt.total_score = objective
    attempt.submitted_at = datetime.utcnow()
    attempt.submission_reason = reason
    attempt.status = AttemptStatus.pending_review if has_short else (AttemptStatus.auto_submitted if reason else AttemptStatus.completed)
    db.commit()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_token(user), "user": public_user(user)}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return public_user(user)


@app.post("/api/users")
def create_user(data: UserCreate, db: Session = Depends(get_db), actor: User = Depends(allow_roles(Role.admin, Role.teacher))):
    if actor.role == Role.teacher and data.role != Role.student:
        raise HTTPException(403, "Teachers may only create student accounts")
    if data.role == Role.student and (not data.department or not data.semester or not data.section):
        raise HTTPException(422, "Student department, semester, and section are required")
    if db.scalar(select(User).where(User.email == data.email.lower())):
        raise HTTPException(409, "Email already exists")
    user = User(name=data.name, email=data.email.lower(), password_hash=hash_password(data.password), role=data.role,
                department=data.department, semester=data.semester, section=data.section.upper() if data.section else None)
    db.add(user)
    db.commit(); db.refresh(user)
    return public_user(user)


@app.get("/api/users")
def list_users(db: Session = Depends(get_db), actor: User = Depends(allow_roles(Role.admin, Role.teacher))):
    query = select(User).order_by(User.created_at.desc())
    if actor.role == Role.teacher:
        query = query.where(User.role == Role.student)
    return [public_user(u) for u in db.scalars(query).all()]


@app.put("/api/users/{user_id}")
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), actor: User = Depends(allow_roles(Role.admin))):
    user = db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    values = data.model_dump(exclude_unset=True)
    if "email" in values:
        values["email"] = str(values["email"]).lower()
        duplicate = db.scalar(select(User).where(User.email == values["email"], User.id != user.id))
        if duplicate: raise HTTPException(409, "Email already exists")
    password = values.pop("password", None)
    if password: user.password_hash = hash_password(password)
    if values.get("section"): values["section"] = values["section"].upper()
    for key, value in values.items(): setattr(user, key, value)
    db.commit(); db.refresh(user)
    return public_user(user)


@app.delete("/api/users/{user_id}")
def deactivate_user(user_id: int, db: Session = Depends(get_db), actor: User = Depends(allow_roles(Role.admin))):
    user = db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    if user.id == actor.id: raise HTTPException(409, "You cannot deactivate your own account")
    user.is_active = False; db.commit()
    return {"message": "Account deactivated"}


@app.get("/api/academic/departments")
def departments(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return [{"id": d.id, "name": d.name, "is_active": d.is_active} for d in db.scalars(select(AcademicDepartment).order_by(AcademicDepartment.name)).all()]


@app.post("/api/academic/departments")
def create_department(data: DepartmentIn, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin))):
    if db.scalar(select(AcademicDepartment).where(AcademicDepartment.name == data.name.strip())): raise HTTPException(409, "Department already exists")
    row = AcademicDepartment(name=data.name.strip(), is_active=data.is_active); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "name": row.name, "is_active": row.is_active}


@app.put("/api/academic/departments/{department_id}")
def update_department(department_id: int, data: DepartmentIn, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin))):
    row = db.get(AcademicDepartment, department_id)
    if not row: raise HTTPException(404, "Department not found")
    old_name = row.name; row.name = data.name.strip(); row.is_active = data.is_active
    for account in db.scalars(select(User).where(User.department == old_name)): account.department = row.name
    for quiz in db.scalars(select(Quiz).where(Quiz.department == old_name)): quiz.department = row.name
    db.commit(); return {"id": row.id, "name": row.name, "is_active": row.is_active}


@app.delete("/api/academic/departments/{department_id}")
def delete_department(department_id: int, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin))):
    row = db.get(AcademicDepartment, department_id)
    if not row: raise HTTPException(404, "Department not found")
    if db.scalar(select(User.id).where(User.department == row.name).limit(1)) or db.scalar(select(Quiz.id).where(Quiz.department == row.name).limit(1)):
        raise HTTPException(409, "Department is assigned to users or quizzes and cannot be deleted")
    db.delete(row); db.commit(); return {"message": "Department deleted"}


@app.get("/api/academic/semesters")
def semesters(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return [{"id": s.id, "number": s.number, "name": s.name, "is_active": s.is_active} for s in db.scalars(select(AcademicSemester).order_by(AcademicSemester.number)).all()]


@app.post("/api/academic/semesters")
def create_semester(data: SemesterIn, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin))):
    if db.scalar(select(AcademicSemester).where(AcademicSemester.number == data.number)): raise HTTPException(409, "Semester already exists")
    row = AcademicSemester(**data.model_dump()); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "number": row.number, "name": row.name, "is_active": row.is_active}


@app.put("/api/academic/semesters/{semester_id}")
def update_semester(semester_id: int, data: SemesterIn, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin))):
    row = db.get(AcademicSemester, semester_id)
    if not row: raise HTTPException(404, "Semester not found")
    old_number = row.number; row.number = data.number; row.name = data.name; row.is_active = data.is_active
    for account in db.scalars(select(User).where(User.semester == old_number)): account.semester = row.number
    for quiz in db.scalars(select(Quiz).where(Quiz.semester == old_number)): quiz.semester = row.number
    db.commit(); return {"id": row.id, "number": row.number, "name": row.name, "is_active": row.is_active}


@app.delete("/api/academic/semesters/{semester_id}")
def delete_semester(semester_id: int, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin))):
    row = db.get(AcademicSemester, semester_id)
    if not row: raise HTTPException(404, "Semester not found")
    if db.scalar(select(User.id).where(User.semester == row.number).limit(1)) or db.scalar(select(Quiz.id).where(Quiz.semester == row.number).limit(1)):
        raise HTTPException(409, "Semester is assigned to users or quizzes and cannot be deleted")
    db.delete(row); db.commit(); return {"message": "Semester deleted"}


@app.get("/api/academic/sections")
def sections(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return [{"id": s.id, "name": s.name, "is_active": s.is_active} for s in db.scalars(select(AcademicSection).order_by(AcademicSection.name)).all()]


@app.post("/api/academic/sections")
def create_section(data: SectionIn, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin))):
    name = data.name.strip().upper()
    if db.scalar(select(AcademicSection).where(AcademicSection.name == name)): raise HTTPException(409, "Section already exists")
    row = AcademicSection(name=name, is_active=data.is_active); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "name": row.name, "is_active": row.is_active}


@app.put("/api/academic/sections/{section_id}")
def update_section(section_id: int, data: SectionIn, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin))):
    row = db.get(AcademicSection, section_id)
    if not row: raise HTTPException(404, "Section not found")
    old_name = row.name; row.name = data.name.strip().upper(); row.is_active = data.is_active
    for account in db.scalars(select(User).where(User.section == old_name)): account.section = row.name
    for quiz in db.scalars(select(Quiz).where(Quiz.section == old_name)): quiz.section = row.name
    db.commit(); return {"id": row.id, "name": row.name, "is_active": row.is_active}


@app.delete("/api/academic/sections/{section_id}")
def delete_section(section_id: int, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin))):
    row = db.get(AcademicSection, section_id)
    if not row: raise HTTPException(404, "Section not found")
    if db.scalar(select(User.id).where(User.section == row.name).limit(1)) or db.scalar(select(Quiz.id).where(Quiz.section == row.name).limit(1)):
        raise HTTPException(409, "Section is assigned to users or quizzes and cannot be deleted")
    db.delete(row); db.commit(); return {"message": "Section deleted"}


@app.post("/api/quizzes")
def create_quiz(data: QuizCreate, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin, Role.teacher))):
    if data.ends_at <= data.starts_at:
        raise HTTPException(422, "Quiz end time must be after its start time")
    quiz = Quiz(title=data.title, description=data.description, creator_id=user.id, department=data.department,
                semester=data.semester, section=data.section.upper(), duration_minutes=data.duration_minutes,
                starts_at=data.starts_at, ends_at=data.ends_at)
    for index, q in enumerate(data.questions):
        question = Question(text=q.text, question_type=q.question_type, marks=q.marks, position=index)
        question.options = [Option(text=o.text, is_correct=o.is_correct) for o in q.options]
        quiz.questions.append(question)
    db.add(quiz); db.commit(); db.refresh(quiz)
    return {"id": quiz.id, "message": "Quiz created as draft"}


@app.get("/api/quizzes")
def quizzes(db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = select(Quiz).options(selectinload(Quiz.creator), selectinload(Quiz.questions).selectinload(Question.options)).order_by(Quiz.created_at.desc())
    if user.role == Role.student:
        query = query.where(Quiz.status == QuizStatus.published, Quiz.department == user.department,
                            Quiz.semester == user.semester, Quiz.section == user.section)
    elif user.role == Role.teacher:
        query = query.where(Quiz.creator_id == user.id)
    return [quiz_dict(q, include_answers=user.role != Role.student) for q in db.scalars(query).unique().all()]


@app.post("/api/quizzes/{quiz_id}/publish")
def publish_quiz(quiz_id: int, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin, Role.teacher))):
    quiz = db.get(Quiz, quiz_id)
    if not quiz: raise HTTPException(404, "Quiz not found")
    ensure_quiz_owner(quiz, user)
    quiz.status = QuizStatus.published; db.commit()
    return {"message": "Quiz published"}


@app.post("/api/quizzes/{quiz_id}/start")
def start_quiz(quiz_id: int, db: Session = Depends(get_db), student: User = Depends(allow_roles(Role.student))):
    quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id).options(selectinload(Quiz.questions).selectinload(Question.options), selectinload(Quiz.creator)))
    now = datetime.utcnow()
    if not quiz or quiz.status != QuizStatus.published: raise HTTPException(404, "Quiz is unavailable")
    if (quiz.department, quiz.semester, quiz.section) != (student.department, student.semester, student.section):
        raise HTTPException(403, "This quiz is not assigned to your class")
    if now < quiz.starts_at or now > quiz.ends_at: raise HTTPException(400, "Quiz is outside its scheduled availability")
    previous = db.scalar(select(Attempt).where(Attempt.quiz_id == quiz.id, Attempt.student_id == student.id).order_by(Attempt.attempt_number.desc()))
    if previous and previous.status == AttemptStatus.in_progress:
        attempt = previous
    elif previous and not previous.retake_allowed:
        raise HTTPException(409, "Quiz already attempted; teacher approval is required for a retake")
    else:
        attempt = Attempt(quiz_id=quiz.id, student_id=student.id, attempt_number=(previous.attempt_number + 1 if previous else 1))
        if previous: previous.retake_allowed = False
        db.add(attempt); db.commit(); db.refresh(attempt)
    deadline = min(quiz.ends_at, attempt.started_at + timedelta(minutes=quiz.duration_minutes))
    return {"attempt_id": attempt.id, "deadline": deadline, "quiz": quiz_dict(quiz)}


@app.put("/api/attempts/{attempt_id}/answers")
def save_answers(attempt_id: int, data: SaveAnswersIn, db: Session = Depends(get_db), student: User = Depends(allow_roles(Role.student))):
    attempt = get_attempt(db, attempt_id)
    if attempt.student_id != student.id or attempt.status != AttemptStatus.in_progress: raise HTTPException(403, "Attempt cannot be edited")
    allowed = {q.id: q for q in attempt.quiz.questions}
    existing = {a.question_id: a for a in attempt.answers}
    for item in data.answers:
        if item.question_id not in allowed: continue
        answer = existing.get(item.question_id) or Answer(attempt_id=attempt.id, question_id=item.question_id)
        answer.selected_option_id = item.selected_option_id
        answer.text_answer = item.text_answer
        db.add(answer)
    db.commit()
    return {"message": "Answers saved"}


@app.post("/api/attempts/{attempt_id}/violation")
def violation(attempt_id: int, data: ViolationIn, db: Session = Depends(get_db), student: User = Depends(allow_roles(Role.student))):
    attempt = get_attempt(db, attempt_id)
    if attempt.student_id != student.id or attempt.status != AttemptStatus.in_progress: raise HTTPException(403, "Attempt is not active")
    attempt.tab_violations += 1
    auto_submitted = attempt.tab_violations >= 3
    if auto_submitted:
        submit_attempt(db, attempt, f"Auto-submitted after {attempt.tab_violations} tab/window switches")
    else: db.commit()
    return {"violations": attempt.tab_violations, "auto_submitted": auto_submitted,
            "message": "Changing tabs is prohibited. A third violation will automatically submit your quiz."}


@app.post("/api/attempts/{attempt_id}/submit")
def submit(attempt_id: int, db: Session = Depends(get_db), student: User = Depends(allow_roles(Role.student))):
    attempt = get_attempt(db, attempt_id)
    if attempt.student_id != student.id: raise HTTPException(403, "Not your attempt")
    submit_attempt(db, attempt)
    max_marks = sum(q.marks for q in attempt.quiz.questions)
    saved_answers = {a.question_id: a for a in attempt.answers}
    review = []
    for question in attempt.quiz.questions:
        if question.question_type != QuestionType.mcq:
            continue
        answer = saved_answers.get(question.id)
        selected = next((o for o in question.options if answer and o.id == answer.selected_option_id), None)
        correct = next((o for o in question.options if o.is_correct), None)
        review.append({
            "question_id": question.id,
            "question": question.text,
            "selected_answer": selected.text if selected else "Not answered",
            "correct_answer": correct.text if correct else "",
            "is_correct": bool(answer and answer.is_correct),
            "awarded_marks": answer.awarded_marks if answer else 0,
            "marks": question.marks,
        })
    return {"status": attempt.status.value, "objective_score": attempt.objective_score, "total_marks": max_marks,
            "message": "Objective result is ready. Final result will be emailed after short answers are reviewed.",
            "review": review}


@app.get("/api/attempts")
def attempts(db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = select(Attempt).options(selectinload(Attempt.quiz).selectinload(Quiz.questions), selectinload(Attempt.student)).order_by(Attempt.started_at.desc())
    if user.role == Role.student: query = query.where(Attempt.student_id == user.id)
    elif user.role == Role.teacher: query = query.join(Quiz).where(Quiz.creator_id == user.id)
    rows = db.scalars(query).unique().all()
    return [{"id": a.id, "quiz_id": a.quiz_id, "quiz_title": a.quiz.title, "student_name": a.student.name,
             "status": a.status.value, "objective_score": a.objective_score, "manual_score": a.manual_score,
             "total_score": a.total_score, "total_marks": sum(q.marks for q in a.quiz.questions),
             "tab_violations": a.tab_violations, "submission_reason": a.submission_reason,
             "retake_allowed": a.retake_allowed} for a in rows]


@app.get("/api/attempts/{attempt_id}")
def attempt_detail(attempt_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    attempt = get_attempt(db, attempt_id)
    if user.role == Role.student and attempt.student_id != user.id: raise HTTPException(403, "Not your attempt")
    if user.role == Role.teacher: ensure_quiz_owner(attempt.quiz, user)
    answers = {a.question_id: a for a in attempt.answers}
    return {"id": attempt.id, "student": public_user(attempt.student), "quiz": quiz_dict(attempt.quiz, include_answers=user.role != Role.student),
            "status": attempt.status.value, "objective_score": attempt.objective_score, "manual_score": attempt.manual_score,
            "total_score": attempt.total_score, "submission_reason": attempt.submission_reason,
            "answers": [{"id": a.id, "question_id": a.question_id, "text_answer": a.text_answer,
                         "selected_option_id": a.selected_option_id, "awarded_marks": a.awarded_marks,
                         "feedback": a.teacher_feedback} for a in answers.values()]}


@app.put("/api/answers/{answer_id}/grade")
def grade_answer(answer_id: int, data: GradeIn, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin, Role.teacher))):
    answer = db.scalar(select(Answer).where(Answer.id == answer_id).options(selectinload(Answer.question), selectinload(Answer.attempt).selectinload(Attempt.quiz)))
    if not answer or answer.question.question_type != QuestionType.short: raise HTTPException(404, "Short answer not found")
    ensure_quiz_owner(answer.attempt.quiz, user)
    if data.awarded_marks > answer.question.marks: raise HTTPException(422, "Awarded marks exceed question marks")
    answer.awarded_marks = data.awarded_marks; answer.teacher_feedback = data.feedback
    db.commit()
    return {"message": "Answer graded"}


@app.post("/api/attempts/{attempt_id}/finalize")
def finalize(attempt_id: int, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin, Role.teacher))):
    attempt = get_attempt(db, attempt_id); ensure_quiz_owner(attempt.quiz, user)
    if attempt.status == AttemptStatus.completed:
        raise HTTPException(409, "This final result has already been published")
    short_ids = {q.id for q in attempt.quiz.questions if q.question_type == QuestionType.short}
    short_answers = [a for a in attempt.answers if a.question_id in short_ids]
    if any(a.awarded_marks is None for a in short_answers): raise HTTPException(409, "Grade every submitted short answer first")
    attempt.manual_score = sum(a.awarded_marks or 0 for a in short_answers)
    attempt.total_score = attempt.objective_score + attempt.manual_score
    attempt.status = AttemptStatus.completed
    max_marks = sum(q.marks for q in attempt.quiz.questions)
    answer_map = {a.question_id: a for a in attempt.answers}
    email_details = []
    for question in attempt.quiz.questions:
        answer = answer_map.get(question.id)
        if question.question_type == QuestionType.mcq:
            selected = next((o for o in question.options if answer and o.id == answer.selected_option_id), None)
            correct = next((o for o in question.options if o.is_correct), None)
            email_details.append({"type": "mcq", "question": question.text,
                                  "student_answer": selected.text if selected else "Not answered",
                                  "correct_answer": correct.text if correct else "",
                                  "is_correct": bool(answer and answer.is_correct),
                                  "awarded_marks": answer.awarded_marks if answer else 0, "marks": question.marks})
        else:
            awarded = answer.awarded_marks if answer and answer.awarded_marks is not None else 0
            email_details.append({"type": "short", "question": question.text,
                                  "student_answer": answer.text_answer if answer else "Not answered",
                                  "correct_answer": "", "is_correct": awarded >= question.marks,
                                  "awarded_marks": awarded, "marks": question.marks,
                                  "feedback": answer.teacher_feedback if answer else ""})
    emailed = send_result_email(attempt.student.email, attempt.student.name, attempt.quiz.title,
                                attempt.total_score, max_marks, attempt.objective_score,
                                attempt.manual_score, email_details)
    attempt.final_email_sent = emailed
    db.commit()
    return {"message": "Final result published" + (" and emailed" if emailed else "; SMTP is not configured"), "score": attempt.total_score}


@app.post("/api/attempts/{attempt_id}/allow-retake")
def allow_retake(attempt_id: int, db: Session = Depends(get_db), user: User = Depends(allow_roles(Role.admin, Role.teacher))):
    attempt = get_attempt(db, attempt_id); ensure_quiz_owner(attempt.quiz, user)
    attempt.retake_allowed = True; db.commit()
    return {"message": "Student may retake this quiz once"}
