import os
import logging
from dotenv import load_dotenv

load_dotenv()

# -------------------------
# Website
# -------------------------

TENDER_SITES = [
    {
        "name": "SPMCIL Corporate",
        "type": "corporate",
        "url": "https://www.spmcil.com/en/tenders/"
    },
    {
        "name": "IGM Mumbai",
        "type": "unit",
        "url": "https://igmmumbai.spmcil.com/en/latest-tenders/"
    },
    {
        "name": "IGM Kolkata",
        "type": "unit",
        "url": "https://igmkolkata.spmcil.com/en/latest-tenders/"
    },
    {
        "name": "IGM Hyderabad",
        "type": "unit",
        "url": "https://igmhyderabad.spmcil.com/en/latest-tenders/"
    },
    {
        "name": "IGM Noida",
        "type": "unit",
        "url": "https://igmnoida.spmcil.com/en/latest-tenders/"
    },
    {
        "name": "CNP Nashik",
        "type": "unit",
        "url": "https://cnpnashik.spmcil.com/en/latest-tenders/"
    },
    {
        "name": "BNP Dewas",
        "type": "unit",
        "url": "https://bnpdewas.spmcil.com/en/latest-tenders/"
    },
    {
        "name": "ISP Nashik",
        "type": "unit",
        "url": "https://ispnasik.spmcil.com/en/latest-tenders/"
    },
    {
        "name": "SSP Hyderabad",
        "type": "unit",
        "url": "https://spphyderabad.spmcil.com/en/latest-tenders/"
    },
    {
        "name": "SPM Narmadapuram",
        "type": "unit",
        "url": "https://spmnarmadapuram.spmcil.com/en/latest-tenders/"
    },
    {
        "name": "BRBNMPL",
        "url": "https://www.brbnmpl.co.in/tender/",
        "type": "brbnmpl"
    },

    {
        "name": "BNPM India",
        "url": "https://www.bnpmindia.com/ViewActiveTender.aspx",
        "type": "bnpm"
    }
]

# -------------------------
# Google Sheet
# -------------------------

GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")

#tender keywords
KEYWORDS = [
    "Security Thread",
    "Fibre",
    "Pasaban Spares",
    "Third party IT",
    "Voith  Spare",
    "Isra Vision",
    "CNC Machine",
    "Clextral",
    "Schoen",
    "Schoen + Sandt",
    "Sandt",
    "Isravision",
    "Voith",
    "Bivis",
    "Lang",
    "Shitter",
    "Sheeter",
    "PM 5",
    "PM 6",
    "Security Thread",
    "Fibres",
    "Fibers",
    "BCLP",
    'BCCP',
    "HAUV",
    "Buckram",
    "Passport",
    "Intaglio Ink",
    "Fluorescent Ink",
    "Pasaban",
    "Komsco",
    "Cotton Comber",
    "UPS",
    "PVA",
    "Polyvinyl Alcohol",
    "Schuler",
    "Vinsak",
]


# -------------------------
# Frontend
# -------------------------

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
)


# -------------------------
# Security & CORS
# -------------------------

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "spmcil-tender-monitoring-default-secret-change-in-production"
)

raw_cors = os.getenv("CORS_ORIGINS", "")
if raw_cors:
    CORS_ORIGINS = [o.strip() for o in raw_cors.split(",") if o.strip()]
else:
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        FRONTEND_URL
    ]

# -------------------------
# Email
# -------------------------

EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

MAIL_FROM = os.getenv(
    "MAIL_FROM",
    EMAIL_SENDER
)

# -------------------------
# Production Logging
# -------------------------

LOG_DIR = "logs"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

from logging.handlers import RotatingFileHandler

class SafeRotatingFileHandler(RotatingFileHandler):
    """
    Cross-platform rotating file handler that gracefully handles
    Windows file lock contention during rollover.
    """
    def doRollover(self):
        try:
            super().doRollover()
        except (PermissionError, OSError):
            pass

logger = logging.getLogger("tender_monitoring")
logger.setLevel(logging.INFO)

if not logger.handlers:
    # Rotating file handler: 10MB per file, max 5 backup files
    file_handler = SafeRotatingFileHandler(
        filename=os.path.join(LOG_DIR, "app.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
        delay=True
    )
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console stream handler for Docker and terminal output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)