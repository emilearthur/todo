"""Function to send Email."""

import email.message
import smtplib
from typing import List

from pydantic import EmailStr

from app.core.config import EMAIL_ADDR, EMAIL_PWD


class EmailService:
    """Class to send Emal."""

    async def send_email_gmail(self, *, emails: List[EmailStr], username: str, generated_code: str):
        """Send email to user."""
        email_content = f"""
                        <html>
                        <body>
                        <p>Hello {username}, Your  email verification code is {generated_code}
                        <br>Thanks for using our Todo Application.</p>
                        </body>
                        </html>
                     """
        message = email.message.Message()
        message["Subject"] = 'Todo App Authentication'
        message["From"] = EMAIL_ADDR

        message.add_header('Content-Type', 'text/html')
        message.set_payload(email_content)
        client = smtplib.SMTP('smtp.gmail.com: 587')
        client.starttls()

        # Login Credentials to send the mail.
        client.login(message["From"], EMAIL_PWD)

        for user_email in emails:
            client.sendmail(message["From"], user_email, message.as_string())
            print(f"sending to {user_email}")
