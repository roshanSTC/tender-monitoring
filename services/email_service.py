import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config


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

        html = f"""
        <html>
        <body style="font-family:Arial,sans-serif">

            <h2>Hello {name},</h2>

            <p>
                You have been invited to
                <strong>Tender Monitoring System</strong>.
            </p>
            

            <p>
                {token}
            </p>
            <p>
                Click the button below to set your password.
            </p>

            <p>
                <a
                    href="{invitation_link}"
                    style="
                        background:#2563eb;
                        color:white;
                        padding:12px 20px;
                        text-decoration:none;
                        border-radius:6px;
                    "
                >
                    Set Password
                </a>
            </p>

            <p>
                This invitation will expire in
                <strong>48 hours</strong>.
            </p>

            <hr>

            <small>
                If you didn't expect this email,
                you can safely ignore it.
            </small>

        </body>
        </html>
        """

        return EmailService.send_email(
            email,
            "Invitation to Tender Monitoring System",
            html,
        )