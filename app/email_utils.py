import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "alert@foodwastezero.com")


def send_email(to_email: str, subject: str, html_content: str):
    if not SENDGRID_API_KEY:
        print("❌ SendGrid API key manquante — email non envoyé.")
        return False

    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        print("📨 SendGrid response status:", response.status_code)
        print("📨 SendGrid response body:", response.body)
        print("📨 SendGrid response headers:", response.headers)

        return True
    except Exception as e:
        print("❌ Erreur envoi email:", e)
        return False
