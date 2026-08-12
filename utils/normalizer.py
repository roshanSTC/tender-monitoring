from datetime import datetime
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

        if value is None:
            return None

        if isinstance(value, datetime):
            return value.date()

        if hasattr(value, "date"):
            return value.date()

        if isinstance(value, str):

            value = value.strip()

            formats = [

                "%d-%b-%Y",

                "%d/%m/%Y",

                "%d-%m-%Y",

                "%Y-%m-%d",

            ]

            for fmt in formats:

                try:

                    return datetime.strptime(
                        value,
                        fmt,
                    ).date()

                except ValueError:

                    continue

        return None