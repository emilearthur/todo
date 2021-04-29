"""Routes for email verification."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi_mail import FastMail

from app.api.dependencies.auth import get_current_active_user
from app.models.email_verfication import (EmailSchema, EmailVerficationCreate,
                                          EmailVerficationInDB,
                                          EmailVerificationUpdate)
from app.models.user import UserInDB

router = APIRouter()

generated_code = "xxxx"        # function that generates code

email_html = f"""
    <html>
    <body>
    <p>Hello There, Your  email verification code is {generated_code}
    <br>Thanks for using our Todo Application.</p>
    </body>
    </html>
"""


@router.post("/email/")
async def send_email(current_user: UserInDB = Depends(get_current_active_user)) -> JSONResponse:
    """Send verification email to user."""
    # TODO: add email and password from config and get form there.
    mail = FastMail(email="xxx@gmail.com", password="mypassword", tls=True, port="587", service="gmail")

    await mail.send_message(recipient=current_user.email, subject="Email Verification", body=email_html, text_format="html")
    return JSONResponse(status_code=200, content={"message": f"email has been sent {current_user.email} address"})