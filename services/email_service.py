import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config
from services.template_service import TemplateService


class EmailService:

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html: str,
    ):

        try:

            message = MIMEMultipart("alternative")

            message["Subject"] = subject
            message["From"] = config.MAIL_FROM
            message["To"] = to_email

            message.attach(
                MIMEText(html, "html")
            )

            smtp = smtplib.SMTP(
                config.SMTP_SERVER,
                config.SMTP_PORT,
            )

            smtp.starttls()

            smtp.login(
                config.EMAIL_SENDER,
                config.EMAIL_PASSWORD,
            )

            smtp.sendmail(
                config.EMAIL_SENDER,
                to_email,
                message.as_string(),
            )

            smtp.quit()

            return True

        except Exception as e:

            config.logger.exception(
                f"Email sending failed: {e}"
            )

            return False

    @staticmethod
    def send_invitation_email(
        email: str,
        name: str,
        token: str,
    ):

        invitation_link = (
            f"{config.FRONTEND_URL}"
            f"/set-password?token={token}"
        )

        html = TemplateService.render(
            "emails/invitation.html",
            name=name,
            token=token,
            invitation_link=invitation_link,
        )

        return EmailService.send_email(
            email,
            "Invitation to Tender Monitoring System",
            html,
        )
        
    @staticmethod
    def send_corrigendum_email(
        email: str,
        template_data: dict,
    ):

        from services.template_service import TemplateService

        html = TemplateService.render(
            "emails/corrigendum.html",
            **template_data
        )

        return EmailService.send_email(
            email,
            "Corrigendum Alert",
            html,
        )