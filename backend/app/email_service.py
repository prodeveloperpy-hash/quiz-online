import smtplib
from html import escape
from email.message import EmailMessage
from .config import settings


def send_result_email(to_email: str, student_name: str, quiz_title: str, score: float, total: float,
                      objective_score: float = 0, manual_score: float = 0,
                      details: list[dict] | None = None) -> bool:
    details = details or []
    if not settings.smtp_email or not settings.smtp_app_password:
        print(f"[EMAIL DISABLED] {to_email}: {quiz_title} — {score}/{total}")
        return False
    percentage = round((score / total * 100) if total else 0, 1)
    passed = percentage >= 50
    rows = []
    text_rows = []
    for index, item in enumerate(details, 1):
        is_correct = item.get("is_correct", False)
        status = "Correct" if is_correct else ("Reviewed" if item.get("type") == "short" else "Incorrect")
        color = "#087469" if is_correct else ("#8a5a00" if item.get("type") == "short" else "#b42318")
        background = "#edf9f4" if is_correct else ("#fff8e8" if item.get("type") == "short" else "#fff1f0")
        correct_block = ""
        if not is_correct and item.get("correct_answer"):
            correct_block = f'<div style="margin-top:7px;color:#087469"><b>Correct answer:</b> {escape(str(item["correct_answer"]))}</div>'
        feedback_block = ""
        if item.get("feedback"):
            feedback_block = f'<div style="margin-top:7px;color:#52616b"><b>Teacher feedback:</b> {escape(str(item["feedback"]))}</div>'
        rows.append(f"""
          <tr><td style="padding:0 0 12px">
            <div style="border:1px solid #dfe7ea;border-left:4px solid {color};border-radius:10px;padding:16px;background:{background}">
              <div style="display:flex;justify-content:space-between;gap:16px">
                <b style="color:#172b3a">{index}. {escape(str(item.get('question', 'Question')))}</b>
                <span style="white-space:nowrap;color:{color};font-weight:700">{status} · {item.get('awarded_marks', 0)}/{item.get('marks', 0)}</span>
              </div>
              <div style="margin-top:9px;color:#52616b"><b>Your answer:</b> {escape(str(item.get('student_answer') or 'Not answered'))}</div>
              {correct_block}{feedback_block}
            </div>
          </td></tr>""")
        text_rows.append(f"{index}. {item.get('question')}\n   Status: {status} ({item.get('awarded_marks', 0)}/{item.get('marks', 0)})\n   Your answer: {item.get('student_answer') or 'Not answered'}" +
                         (f"\n   Correct answer: {item.get('correct_answer')}" if not is_correct and item.get('correct_answer') else "") +
                         (f"\n   Teacher feedback: {item.get('feedback')}" if item.get('feedback') else ""))
    message = EmailMessage()
    message["Subject"] = f"Final result — {quiz_title}"
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_email}>"
    message["To"] = to_email
    message.set_content(
        f"Dear {student_name},\n\nYour final result for {quiz_title} is {score}/{total} ({percentage}%).\n"
        f"Objective score: {objective_score}\nManual score: {manual_score}\n\n" + "\n\n".join(text_rows) +
        "\n\nThis result includes the teacher's manual evaluation of short answers.\n\nQuiz Online"
    )
    message.add_alternative(f"""<!doctype html><html><body style="margin:0;background:#eef3f5;font-family:Arial,sans-serif;color:#172b3a">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0"><tr><td align="center" style="padding:32px 12px">
        <table role="presentation" width="680" cellspacing="0" cellpadding="0" style="max-width:680px;width:100%;background:white;border-radius:16px;overflow:hidden;box-shadow:0 12px 35px rgba(9,45,66,.12)">
          <tr><td style="background:linear-gradient(135deg,#092d42,#078a83);padding:30px;color:white">
            <div style="font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#8ee0d3">University Assessment Portal</div>
            <h1 style="margin:8px 0 0;font-size:28px">Quiz Online</h1>
          </td></tr>
          <tr><td style="padding:30px">
            <p style="margin-top:0;color:#52616b">Dear {escape(student_name)},</p>
            <h2 style="margin:5px 0">{escape(quiz_title)}</h2>
            <p style="color:#687986">Your complete result has been reviewed and published.</p>
            <table role="presentation" width="100%" cellspacing="8" cellpadding="0" style="margin:20px -8px">
              <tr>
                <td style="background:#f1f7f7;border-radius:10px;padding:16px"><small style="color:#687986">FINAL SCORE</small><div style="font-size:24px;font-weight:800">{score}/{total}</div></td>
                <td style="background:#f1f7f7;border-radius:10px;padding:16px"><small style="color:#687986">PERCENTAGE</small><div style="font-size:24px;font-weight:800">{percentage}%</div></td>
                <td style="background:{'#edf9f4' if passed else '#fff1f0'};border-radius:10px;padding:16px"><small style="color:#687986">STATUS</small><div style="font-size:24px;font-weight:800;color:{'#087469' if passed else '#b42318'}">{'PASS' if passed else 'REVIEW'}</div></td>
              </tr>
            </table>
            <div style="padding:13px 16px;background:#f7f9fa;border-radius:9px;margin-bottom:22px;color:#52616b"><b>Objective:</b> {objective_score} &nbsp;·&nbsp; <b>Manual:</b> {manual_score}</div>
            <h3 style="border-bottom:1px solid #dfe7ea;padding-bottom:10px">Question breakdown</h3>
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">{''.join(rows)}</table>
            <p style="margin:24px 0 0;padding-top:18px;border-top:1px solid #dfe7ea;color:#7a8991;font-size:12px">This is an automated result notification from Quiz Online.</p>
          </td></tr>
        </table>
      </td></tr></table>
    </body></html>""", subtype="html")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_email, settings.smtp_app_password)
        server.send_message(message)
    return True
