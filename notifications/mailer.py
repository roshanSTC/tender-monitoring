"""
mailer.py

Sends email notifications for newly added tenders.
"""
from services.active_tenders import count_active_tenders
from collections import defaultdict
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (
    EMAIL_SENDER,
    EMAIL_PASSWORD,
    EMAIL_RECEIVER,
    SMTP_SERVER,
    SMTP_PORT,
    logger,
)


class TenderMailer:

    def __init__(self):

        self.sender = EMAIL_SENDER
        self.password = EMAIL_PASSWORD

        self.receivers = [
            email.strip()
            for email in EMAIL_RECEIVER.split(",")
            if email.strip()
        ]

    # --------------------------------------------------------

    def build_html(self, tenders):

        from collections import defaultdict
        from datetime import datetime

        grouped = defaultdict(list)

        # --------------------------------------------------
        # Group matched tenders by source
        # --------------------------------------------------

        for tender in tenders:

            grouped[
                tender.get("Source", "Unknown")
            ].append(tender)

        # --------------------------------------------------
        # Start HTML
        # --------------------------------------------------

        html = """
        <h3 style="
            color:#2F5597;
            font-family:Arial, sans-serif;
            margin-top:20px;
            margin-bottom:10px;
        ">
            Matching Tender Details
        </h3>
        """

        today = datetime.now().date()

        # --------------------------------------------------
        # Supported date formats
        # --------------------------------------------------

        date_formats = [

            "%d %b %Y %I:%M %p",
            "%d %B %Y %I:%M %p",

            "%d %b %Y",
            "%d %B %Y",

            "%d/%m/%Y",
            "%d-%m-%Y",

            "%d/%m/%Y %I:%M %p",
            "%d-%m-%Y %I:%M %p",

        ]

        # ==================================================
        # GROUP BY SOURCE
        # ==================================================

        for source, source_tenders in grouped.items():

            html += f"""

            <h3 style="
                background:#2F5597;
                color:white;
                padding:10px;
                border-radius:4px;
                margin-top:20px;
                margin-bottom:8px;
                font-family:Arial, sans-serif;
            ">

                🏢 {source}

                &nbsp;

                <span style="
                    background:white;
                    color:#2F5597;
                    padding:3px 8px;
                    border-radius:12px;
                    font-size:12px;
                    font-weight:bold;
                ">

                    {len(source_tenders)} Tender(s)

                </span>

            </h3>


            <table border="1"
                cellspacing="0"
                cellpadding="6"
                style="
                    border-collapse:collapse;
                    width:100%;
                    margin-bottom:25px;
                    font-family:Arial, sans-serif;
                    font-size:13px;
                ">

                <tr style="background:#D9EAD3;">

                    <th>
                        Tender Number
                    </th>

                    <th>
                        Tender Title
                    </th>

                    <th>
                        Keyword
                    </th>

                    <th>
                        Publishing Date
                    </th>

                    <th>
                        Closing Date
                    </th>

                    <th>
                        Days Left
                    </th>

                    <th>
                        Tender
                    </th>

                    <th>
                        Corrigendum
                    </th>

                </tr>

            """

            # ==================================================
            # EACH MATCHED TENDER
            # ==================================================

            for tender in source_tenders:

                # --------------------------------------------------
                # Get closing date
                # --------------------------------------------------

                closing_date = tender.get(
                    "Closing Date",
                    ""
                )

                if closing_date:

                    closing_date = closing_date.strip()

                else:

                    closing_date = ""

                closing = None

                # --------------------------------------------------
                # Parse closing date
                # --------------------------------------------------

                for date_format in date_formats:

                    try:

                        closing = datetime.strptime(
                            closing_date,
                            date_format
                        )

                        break

                    except ValueError:

                        continue

                # --------------------------------------------------
                # Calculate days left
                # --------------------------------------------------

                days_left = None

                if closing:

                    days_left = (
                        closing.date() - today
                    ).days

                # --------------------------------------------------
                # Days Left HTML
                # --------------------------------------------------

                if days_left is None:

                    days_left_html = """
                    <span style="
                        color:#777;
                        font-weight:bold;
                    ">
                        -
                    </span>
                    """

                elif days_left < 0:

                    days_left_html = """
                    <span style="
                        color:#C00000;
                        font-weight:bold;
                    ">
                        Expired
                    </span>
                    """

                elif days_left == 0:

                    days_left_html = """
                    <span style="
                        color:#C00000;
                        font-weight:bold;
                    ">
                        Today
                    </span>
                    """

                elif days_left <= 3:

                    days_left_html = f"""
                    <span style="
                        color:#C00000;
                        font-weight:bold;
                    ">
                        {days_left} day(s)
                    </span>
                    """

                elif days_left <= 7:

                    days_left_html = f"""
                    <span style="
                        color:#E69138;
                        font-weight:bold;
                    ">
                        {days_left} day(s)
                    </span>
                    """

                else:

                    days_left_html = f"""
                    <span style="
                        color:green;
                        font-weight:bold;
                    ">
                        {days_left} day(s)
                    </span>
                    """

                # --------------------------------------------------
                # Tender
                # --------------------------------------------------

                tender_doc = "-"

                tender_Tender_url = tender.get(
                    "Tender URL",
                    ""
                )

                if tender_Tender_url:

                    tender_doc = f"""
                    <a
                        href="{tender_Tender_url}"
                        target="_blank"
                        style="
                            color:#1155CC;
                            text-decoration:none;
                            font-weight:bold;
                        "
                    >
                        Download
                    </a>
                    """

                # --------------------------------------------------
                # Corrigendum
                # --------------------------------------------------

                corrigendum = "-"

                corrigendum_url = tender.get(
                    "Corrigendum URL",
                    ""
                )

                if corrigendum_url:

                    corrigendum = f"""
                    <a
                        href="{corrigendum_url}"
                        target="_blank"
                        style="
                            color:#1155CC;
                            text-decoration:none;
                            font-weight:bold;
                        "
                    >
                        View
                    </a>
                    """

                # --------------------------------------------------
                # Tender Row
                # --------------------------------------------------

                html += f"""

                <tr>

                    <td>
                        {tender.get(
                            "Tender Number",
                            ""
                        )}
                    </td>

                    <td>
                        {tender.get(
                            "Tender Title",
                            ""
                        )}
                    </td>

                    <td>
                        <b>
                            {tender.get(
                                "Matched Keyword",
                                "-"
                            )}
                        </b>
                    </td>

                    <td>
                        {tender.get(
                            "Publishing Date",
                            ""
                        )}
                    </td>

                    <td>
                        {tender.get(
                            "Closing Date",
                            ""
                        )}
                    </td>

                    <td align="center">

                        {days_left_html}

                    </td>

                    <td align="center">

                        {tender_doc}

                    </td>

                    <td align="center">

                        {corrigendum}

                    </td>

                </tr>

                """

            # --------------------------------------------------
            # Close source table
            # --------------------------------------------------

            html += """

            </table>

            """

        # --------------------------------------------------
        # Return only tender HTML
        # --------------------------------------------------

        return html

    # --------------------------------------------------------

    def send_health_report(self, summary):

        try:

            message = MIMEMultipart("alternative")

            message["Subject"] = (
                "✅ Tender Monitor | Daily Scan Completed (No Matches)"
            )

            message["From"] = self.sender

            message["To"] = ", ".join(self.receivers)

            html = f"""
            <html>

            <body style="font-family:Arial, sans-serif;">

                <h2 style="color:#2F5597;">
                    ✅ Daily Health Report
                </h2>

                <p>
                    The tender monitoring process completed successfully.
                    No tenders matched the configured keywords.
                </p>

                <table border="1"
                    cellspacing="0"
                    cellpadding="8"
                    style="
                        border-collapse:collapse;
                        width:60%;
                        font-size:14px;
                    ">

                    <tr style="background:#D9EAD3;">
                        <th align="left">Metric</th>
                        <th align="left">Value</th>
                    </tr>

                    <tr>
                        <th align="left">Total Websites</th>
                        <td>{summary["total_websites"]}</td>
                    </tr>

                    <tr>
                        <th align="left">Active Tenders</th>
                        <td>{summary["active_tenders"]}</td>
                    </tr>

                    <tr>
                        <th align="left">Existing Tenders</th>
                        <td>{summary["existing_tenders"]}</td>
                    </tr>

                    <tr>
                        <th align="left">New Tenders</th>
                        <td>{summary["new_tenders"]}</td>
                    </tr>

                </table>

                <br>

                <p style="color:green;">
                    ✔ Monitoring system is operating normally.
                </p>

                <hr>

                <p style="font-size:12px;color:gray;">

                    This is an automated email generated by the
                    <b>Tender Monitoring System</b>.

                </p>

            </body>

            </html>
            """

            message.attach(
                MIMEText(html, "html")
            )

            server = smtplib.SMTP(
                SMTP_SERVER,
                SMTP_PORT
            )

            server.starttls()

            server.login(
                self.sender,
                self.password
            )

            server.sendmail(
                self.sender,
                self.receivers,
                message.as_string()
            )

            server.quit()

            logger.info(
                "Health report sent successfully."
            )

            print(
                "Health report sent successfully."
            )

        except Exception as e:

            logger.exception(e)

            print(
                f"Health report email failed: {e}"
            )


    def send_email(self, tenders, summary):

        if not tenders:

            logger.info(
                "No keyword matched tenders."
            )

            print(
                "No email sent."
            )

            return

        try:

            message = MIMEMultipart("alternative")

            message["Subject"] = (
                f"🚨 SPMCIL Tender Alert "
                f"({len(tenders)} Matching Tender(s))"
            )

            message["From"] = self.sender

            message["To"] = ", ".join(
                self.receivers
            )

            # --------------------------------------------------
            # Summary section
            # --------------------------------------------------

            summary_html = f"""
            <h2 style="color:#C00000;">
                🚨 Tender Alert
            </h2>

            <p>
                New keyword-matching tenders have been detected.
            </p>

            <table border="1"
                cellspacing="0"
                cellpadding="8"
                style="
                    border-collapse:collapse;
                    width:60%;
                    font-size:14px;
                ">

                <tr style="background:#F4CCCC;">

                    <th align="left">
                        Metric
                    </th>

                    <th align="left">
                        Value
                    </th>

                </tr>

                <tr>

                    <th align="left">
                        Total Websites
                    </th>

                    <td>
                        {summary["total_websites"]}
                    </td>

                </tr>

                <tr>

                    <th align="left">
                        Total New Tenders
                    </th>

                    <td>
                        {summary["new_tenders"]}
                    </td>

                </tr>
                <tr>

                    <th align="left">
                        Total Active Tenders
                    </th>

                    <td>
                        {summary["active_tenders"]}
                    </td>

                </tr>

                <tr>

                    <th align="left">
                        Matched Keywords
                    </th>

                    <td>
                        {summary["keyword_matches"]}
                    </td>

                </tr>

                <tr>

                    <th align="left">
                        Existing Tenders
                    </th>

                    <td>
                        {summary["existing_tenders"]}
                    </td>

                </tr>

            </table>

            <br>

            <hr>
            """

            # --------------------------------------------------
            # Existing tender table
            # --------------------------------------------------

            tender_html = self.build_html(
                tenders
            )

            # Remove duplicate HTML header if build_html
            # contains its own <html>/<body>.
            #
            # Better approach: use only the table portion
            # later if you want to make the email cleaner.

            html = f"""
            <html>

            <body style="font-family:Arial, sans-serif;">

                {summary_html}

                {tender_html}

            </body>

            </html>
            """

            message.attach(
                MIMEText(html, "html")
            )

            server = smtplib.SMTP(
                SMTP_SERVER,
                SMTP_PORT
            )

            server.starttls()

            server.login(
                self.sender,
                self.password
            )

            server.sendmail(
                self.sender,
                self.receivers,
                message.as_string()
            )

            server.quit()

            logger.info(
                "Tender alert email sent successfully."
            )

            print(
                "Tender alert email sent successfully."
            )

        except Exception as e:

            logger.exception(e)

            print(
                f"Tender alert email failed: {e}"
            )
            
    def send_user_email(
        self,
        recipient_email,
        subject,
        html_body,
    ):

        try:

            message = MIMEMultipart("alternative")

            message["Subject"] = subject
            message["From"] = self.sender
            message["To"] = recipient_email

            message.attach(
                MIMEText(
                    html_body,
                    "html"
                )
            )

            server = smtplib.SMTP(
                SMTP_SERVER,
                SMTP_PORT
            )

            server.starttls()

            server.login(
                self.sender,
                self.password
            )

            server.sendmail(
                self.sender,
                [recipient_email],
                message.as_string()
            )

            server.quit()

            logger.info(
                f"User email sent successfully to {recipient_email}"
            )

            print(
                f"User email sent successfully to {recipient_email}"
            )

            return True

        except Exception as e:

            logger.exception(e)

            print(
                f"User email failed for {recipient_email}: {e}"
            )

            return False