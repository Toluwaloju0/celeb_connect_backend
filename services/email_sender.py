""" a module to create a function to send email to a user"""

import smtplib

from os import getenv
from email.message import EmailMessage

from models.otp_codes_model import OtpCode
from database.storage_engine import storage
from utils.create_otp_code import create_otp
from utils.responses import function_response

class EmailSender:
    """ a class which holds functions to send emails to a user"""

    def __init__(self):
        """ the class initializer"""

        self.__sender = smtplib("smtp.gmail.com", 587)
        self.__sender.starttls()
        account = getenv("GOOGLE_ACCOUNT")
        password = getenv("GOOGLE_PASSWORD")

        self.sender.login(account, password)

    def send_otp_code(self, email_address: str):
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
            otp_code_object += 1
        else:
            otp_code_object = OtpCode(email_address, otp_code)
        otp_code_object.save()

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
""")
        
        self.__sender.send_message(message)

        return function_response(True, {"code": otp_code})
    
    def delete_otp_code(self, otp_object):
        """ a method to delete otp codes from the database
        Args:
            email_address (str): the email address bearing the code
        """

        storage.delete_otp_code_object(otp_object)

    def get_otp_email(self, code: str):
        """ a method to get the email associated with the provided otp code
        Args:
            code: the otp code
        Return the email associated with the code if found
        """

        otp_object = storage.get_otp_email_object(code)
        return otp_object
    
email_sender = EmailSender()
