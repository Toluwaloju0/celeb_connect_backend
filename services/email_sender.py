""" a module to create a function to send email to a user"""

import smtplib

from os import getenv
from email.message import EmailMessage
from datetime import datetime

from models.otp_codes_model import OtpCode
from database.storage_engine import DBStorage
from utils.create_otp_code import create_otp
from utils.responses import function_response
from utils.id_string import uuid

class EmailSender:
    """ a class which holds functions to send emails to a user"""

    def __init__(self):
        """ the class initializer"""

        self.__sender = smtplib.SMTP("smtp.gmail.com", 587)
        self.__sender.starttls()
        account = getenv("GOOGLE_ACCOUNT")
        password = getenv("GOOGLE_PASSWORD")

        self.__sender.login(account, password)

    def send_otp_code(self, email_address: str, storage: DBStorage):
        """ a method to send otp codes to the provided email address and save the sent otp code to the database
        Args:
            email_address (str): the email address of the user
        Return: the otp object already saved to the database
        """

        otp_code = create_otp()

        saved_otp_response = storage.get_otp_object(email_address)
        if saved_otp_response.status:
            otp_code_object = saved_otp_response.payload
            if otp_code_object.count == 3:
                return function_response(False)
    
            otp_code_object.code = otp_code
            otp_code_object.count += 1
        else:
            otp_code_object = OtpCode(email_address, otp_code)
        otp_code_object.save(storage)

        # send the email to the user
        message = EmailMessage()
        message["To"] = email_address
        message["From"] = getenv("GOOGLE_ACCOUNT")
        message["Subject"] = "Celeb Connect Validation Email"
        message.set_content(f"The validation code is {otp_code}")
        message.add_alternative(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; background-color: #f6f6f6; padding: 20px;">

    <div style="max-width: 500px; margin: auto; background-color: #ffffff; padding: 24px; border-radius: 6px;">
        <h3>Email Verification</h3>

        <p>
            Use the one-time password (OTP) below to verify your email address.
        </p>

        <p style="font-size: 22px; font-weight: bold; letter-spacing: 4px; text-align: center;">
            {otp_code}
        </p>

        <p>
            This code is valid for a short time. Do not share it with anyone.
        </p>

        <p>
            If you did not request this, please ignore this email.
        </p>

        <p>
            Thanks,<br>
            The Team
        </p>
    </div>

</body>
</html>
""", subtype="html")
        
        self.__sender.send_message(message)

        return function_response(True, {"code": otp_code})
    
    def send_agent_password(self, agent_email):
        """a method to send a password to the agent which he needs to change as
        soon as he logs in to the website
        Args:
            agent_email: the email address of the agent
        """

        password = uuid().split("-")[-1]

        message = EmailMessage()
        message["To"] = agent_email
        message["From"] = getenv("GOOGLE_ACCOUNT")
        message["Subject"] = "Celeb Connect Validation Email"
        message.set_content(f"The password is {password}")
        message.add_alternative(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Agent Account Created</title>
</head>
<body style="margin:0; padding:0; background-color:#f4f6f8; font-family:Arial, Helvetica, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td align="center" style="padding:30px 0;">
                <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:8px; box-shadow:0 2px 10px rgba(0,0,0,0.08);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="padding:25px; background:#111827; color:#ffffff; border-radius:8px 8px 0 0;">
                            <h2 style="margin:0; font-size:22px;">Welcome to CelebConnect</h2>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding:30px; color:#333333;">
                            <p style="font-size:15px; line-height:1.6;">
                                Hello,
                            </p>

                            <p style="font-size:15px; line-height:1.6;">
                                Your <strong>Agent account</strong> has been successfully created on
                                <strong>CelebConnect</strong>. You can now manage celebrities, update availability,
                                and handle engagements assigned to you.
                            </p>

                            <p style="font-size:15px; line-height:1.6;">
                                Below are your login credentials:
                            </p>

                            <table cellpadding="0" cellspacing="0" style="margin:20px 0; width:100%;">
                                <tr>
                                    <td style="padding:12px; background:#f9fafb; border:1px solid #e5e7eb;">
                                        <strong>Email:</strong> {agent_email}
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding:12px; background:#f9fafb; border:1px solid #e5e7eb; border-top:none;">
                                        <strong>Password:</strong> {password}
                                    </td>
                                </tr>
                            </table>

                            <p style="font-size:14px; line-height:1.6; color:#6b7280;">
                                For security reasons, please log in and change your password immediately after your
                                first login.
                            </p>

                            <p style="font-size:15px; line-height:1.6;">
                                If you have any questions or need assistance, feel free to contact our support team.
                            </p>

                            <p style="margin-top:30px; font-size:15px;">
                                Best regards,<br>
                                <strong>CelebConnect Team</strong>
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding:20px; background:#f9fafb; color:#6b7280; font-size:12px; text-align:center; border-radius:0 0 8px 8px;">
                            © {datetime.now().year} CelebConnect. All rights reserved.
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
""", subtype="html")
        
        self.__sender.send_message(message)
        return function_response(True, password)

email_sender = EmailSender()
