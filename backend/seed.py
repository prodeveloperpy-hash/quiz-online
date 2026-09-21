from datetime import datetime, timedelta
from sqlalchemy import select
from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import AcademicDepartment, AcademicSection, AcademicSemester, Option, Question, QuestionType, Quiz, Role, User


Base.metadata.create_all(bind=engine)
db = SessionLocal()
accounts = [
    ("System Admin", "admin@onlinequiz.com", "Admin123!", Role.admin, None, None, None, None),
    ("Demo Teacher", "teacher@onlinequiz.com", "Teacher123!", Role.teacher, None, "CS", None, None),
    ("Demo Student", "student@onlinequiz.com", "Student123!", Role.student, "DEMO-001", "CS", 1, "A"),
]
for name, email, password, role, roll_number, department, semester, section in accounts:
    if not db.scalar(select(User).where(User.email == email)):
        db.add(User(name=name, email=email, password_hash=hash_password(password), role=role, roll_number=roll_number,
                    department=department, semester=semester, section=section))
for department in ["CS", "IT", "Software Engineering"]:
    if not db.scalar(select(AcademicDepartment).where(AcademicDepartment.name == department)):
        db.add(AcademicDepartment(name=department))
for number in range(1, 9):
    if not db.scalar(select(AcademicSemester).where(AcademicSemester.number == number)):
        db.add(AcademicSemester(number=number, name=f"Semester {number}"))
for section in ["A", "B"]:
    if not db.scalar(select(AcademicSection).where(AcademicSection.name == section)):
        db.add(AcademicSection(name=section))

db.flush()
teacher = db.scalar(select(User).where(User.email == "teacher@onlinequiz.com"))
demo_quizzes = [
    ("Programming Fundamentals", "Core programming concepts and problem solving.", "CS", 1, "A", [
        ("Which keyword defines a function in Python?", "mcq", 2, [("def", True), ("function", False), ("func", False), ("method", False)]),
        ("Explain the purpose of a loop.", "short", 3, []),
    ]),
    ("Database Basics", "Introduction to relational databases and SQL.", "CS", 1, "A", [
        ("Which SQL command reads records from a table?", "mcq", 2, [("SELECT", True), ("UPDATE", False), ("DELETE", False), ("DROP", False)]),
        ("A primary key uniquely identifies a table row.", "mcq", 2, [("True", True), ("False", False)]),
    ]),
    ("Computer Networks", "Network models, addressing and common protocols.", "IT", 2, "A", [
        ("Which protocol securely transfers web pages?", "mcq", 2, [("HTTPS", True), ("FTP", False), ("SMTP", False), ("DHCP", False)]),
        ("What is the role of an IP address?", "short", 3, []),
    ]),
    ("Software Engineering Principles", "Requirements, design and software lifecycle concepts.", "Software Engineering", 3, "A", [
        ("Which model uses short iterative development cycles?", "mcq", 2, [("Agile", True), ("Waterfall", False), ("V-Model", False), ("Big Bang", False)]),
        ("Why is software testing important?", "short", 3, []),
    ]),
    ("Web Development Essentials", "HTML, CSS and browser fundamentals.", "CS", 1, "A", [
        ("Which language defines the structure of a web page?", "mcq", 2, [("HTML", True), ("CSS", False), ("SQL", False), ("Python", False)]),
        ("CSS is primarily used for page styling.", "mcq", 2, [("True", True), ("False", False)]),
    ]),
]
if teacher:
    for title, description, department, semester, section, question_data in demo_quizzes:
        if db.scalar(select(Quiz).where(Quiz.title == title)):
            continue
        start = datetime.utcnow() + timedelta(days=1)
        quiz = Quiz(title=title, description=description, creator_id=teacher.id, department=department,
                    semester=semester, section=section, duration_minutes=30, starts_at=start,
                    ends_at=start + timedelta(days=1))
        for position, (text, question_type, marks, options) in enumerate(question_data):
            question = Question(text=text, question_type=QuestionType(question_type), marks=marks, position=position)
            question.options = [Option(text=option_text, is_correct=is_correct) for option_text, is_correct in options]
            quiz.questions.append(question)
        db.add(quiz)
db.commit(); db.close()
print("Initial database tables, accounts, and five draft demo quizzes are ready.")
