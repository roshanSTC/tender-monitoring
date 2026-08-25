from datetime import datetime, date
import re
from config import logger
from urllib.parse import urlparse


class TenderNormalizer:

    @staticmethod
    def text(value):

        if value is None:
            return ""

        return (
            str(value)
            .strip()
            .replace("\u00a0", " ")
            .replace("\n", " ")
            .replace("\r", " ")
        )

    @staticmethod
    def url(value):

        value = TenderNormalizer.text(value)

        if not value:
            return ""

        parsed = urlparse(value)

        path = parsed.path.rstrip("/")

        return f"{parsed.scheme}://{parsed.netloc}{path}"

    @staticmethod
    def date(value):
        """
        Normalize tender date/date-time values.

        Production requirements:
        - Supports date-only values.
        - Supports 12-hour and 24-hour formats.
        - Supports slash, dash and space separators.
        - Supports month names.
        - Handles malformed values such as:
              17 Aug 2026 14:00 PM
          by treating 14:00 as 24-hour time.
        - Preserves time information.
        - Never raises an exception for bad source data.
        """

        if value is None:
            return None

        # ------------------------------------------------------
        # Already datetime
        # ------------------------------------------------------

        if isinstance(value, datetime):
            return value

        # ------------------------------------------------------
        # Python date
        # ------------------------------------------------------

        if isinstance(value, date):

            return datetime(
                value.year,
                value.month,
                value.day,
            )

        # ------------------------------------------------------
        # Convert to string
        # ------------------------------------------------------

        if not isinstance(value, str):
            value = str(value)

        value = value.strip()

        if not value:
            return None

        original_value = value

        # ------------------------------------------------------
        # Normalize whitespace
        # ------------------------------------------------------

        value = re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

        # ------------------------------------------------------
        # Normalize common separators
        #
        # Examples:
        #
        # 26/Aug/2026
        # 26-Aug-2026
        # 26 Aug 2026
        # ------------------------------------------------------

        # ------------------------------------------------------
        # SPECIAL CASE:
        #
        # Some BNPM records contain:
        #
        # 17 Aug 2026 14:00 PM
        #
        # This is technically invalid because 14 is already
        # 24-hour time.
        #
        # Treat it as:
        #
        # 17 Aug 2026 14:00
        # ------------------------------------------------------

        malformed_24h_pm = re.search(
            r"(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}"
            r"\s+)(\d{1,2}:\d{2})\s*(AM|PM)$",
            value,
            re.IGNORECASE,
        )

        if malformed_24h_pm:

            time_part = malformed_24h_pm.group(2)

            hour = int(
                time_part.split(":")[0]
            )

            if hour >= 13:

                value = (
                    malformed_24h_pm.group(1)
                    + time_part
                )

                logger.warning(
                    "Normalized malformed 24-hour "
                    f"tender date '{original_value}' "
                    f"to '{value}'"
                )

        # ------------------------------------------------------
        # Supported formats
        # ------------------------------------------------------

        formats = [

            # ==============================================
            # ISO
            # ==============================================

            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",

            # ==============================================
            # Date only
            # ==============================================

            "%Y-%m-%d",

            "%d-%m-%Y",
            "%d/%m/%Y",

            "%d-%b-%Y",
            "%d/%b/%Y",
            "%d %b %Y",

            "%d-%B-%Y",
            "%d/%B/%Y",
            "%d %B %Y",

            # ==============================================
            # Date + 24 hour time
            # ==============================================

            "%d-%m-%Y %H:%M",
            "%d/%m/%Y %H:%M",

            "%d-%b-%Y %H:%M",
            "%d/%b/%Y %H:%M",
            "%d %b %Y %H:%M",

            "%d-%B-%Y %H:%M",
            "%d/%B/%Y %H:%M",
            "%d %B %Y %H:%M",

            # ==============================================
            # Date + 12 hour time
            # ==============================================

            "%d-%m-%Y %I:%M %p",
            "%d/%m/%Y %I:%M %p",

            "%d-%b-%Y %I:%M %p",
            "%d/%b/%Y %I:%M %p",
            "%d %b %Y %I:%M %p",

            "%d-%B-%Y %I:%M %p",
            "%d/%B/%Y %I:%M %p",
            "%d %B %Y %I:%M %p",
            
            "%d/%b/%Y %I:%M %p",

        ]

        # ------------------------------------------------------
        # Try formats
        # ------------------------------------------------------

        for fmt in formats:

            try:

                parsed = datetime.strptime(
                    value,
                    fmt,
                )

                return parsed

            except ValueError:

                continue

        # ------------------------------------------------------
        # ISO fallback
        # ------------------------------------------------------

        try:

            return datetime.fromisoformat(
                value.replace(
                    "Z",
                    "",
                )
            )

        except ValueError:
            pass

        # ------------------------------------------------------
        # Parsing failed
        # ------------------------------------------------------

        logger.warning(
            "Unsupported tender date format: "
            f"'{original_value}'"
        )

        return None