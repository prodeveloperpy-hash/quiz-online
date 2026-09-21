import smtplib
from email.message import EmailMessage
from .config import settings


def send_result_email(to_email: str, student_name: str, quiz_title: str, score: float, total: float) -> bool:
    if not settings.smtp_email or not settings.smtp_app_password:
        print(f"[EMAIL DISABLED] {to_email}: {quiz_title} — {score}/{total}")
        return False
    message = EmailMessage()
    message["Subject"] = f"Final result — {quiz_title}"
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_email}>"
    message["To"] = to_email
    message.set_content(
        f"Dear {student_name},\n\nYour complete result for {quiz_title} is {score}/{total}. "
        "This result includes the teacher's manual evaluation of short answers.\n\nQuiz Online"
    )
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_email, settings.smtp_app_password)
        server.send_message(message)
    return True
