from datetime import datetime, timedelta
from sqlalchemy import select
from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import AcademicDepartment, AcademicSection, AcademicSemester, Role, User


Base.metadata.create_all(bind=engine)
db = SessionLocal()
accounts = [
    ("System Admin", "admin@onlinequiz.com", "Admin123!", Role.admin, None, None, None),
    ("Demo Teacher", "teacher@onlinequiz.com", "Teacher123!", Role.teacher, "CS", None, None),
    ("Demo Student", "student@onlinequiz.com", "Student123!", Role.student, "CS", 1, "A"),
]
for name, email, password, role, department, semester, section in accounts:
    if not db.scalar(select(User).where(User.email == email)):
        db.add(User(name=name, email=email, password_hash=hash_password(password), role=role,
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
db.commit(); db.close()
print("Demo users created.")
