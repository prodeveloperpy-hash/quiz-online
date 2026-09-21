from datetime import datetime, timedelta
from sqlalchemy import select
from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Department, Role, User


Base.metadata.create_all(bind=engine)
db = SessionLocal()
accounts = [
    ("System Admin", "admin@onlinequiz.com", "Admin123!", Role.admin, None, None, None),
    ("Demo Teacher", "teacher@onlinequiz.com", "Teacher123!", Role.teacher, Department.cs, None, None),
    ("Demo Student", "student@onlinequiz.com", "Student123!", Role.student, Department.cs, 1, "A"),
]
for name, email, password, role, department, semester, section in accounts:
    if not db.scalar(select(User).where(User.email == email)):
        db.add(User(name=name, email=email, password_hash=hash_password(password), role=role,
                    department=department, semester=semester, section=section))
db.commit(); db.close()
print("Demo users created.")
