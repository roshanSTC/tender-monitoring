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
    },
    {
        "name": "GeM Portal",
        "url": "https://bidplus.gem.gov.in/all-bids",
        "type": "gem"
    },
    {
        "name": "eProcure Portal (CPPP)",
        "url": "https://eprocure.gov.in/eprocure/app",
        "type": "gepnic"
    },
    {
        "name": "eTenders Portal",
        "url": "https://etenders.gov.in/eprocure/app",
        "type": "gepnic"
    }
]

# -------------------------
# Supabase Configuration
# -------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "tenders")

# -------------------------
# Google Sheet (Legacy / Backup)
# -------------------------

GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")

# tender keywords
KEYWORDS = [
    "CNC Machine",
    "E-Type Machine",
    "Rimming Machine",
    "Opacified Polymer Substrate Sheets",
    "Physical Vapour Deposition System",
    "Security Design Software",
    "ICAO Compliant Electronic Contactless Inlays",
    "CTOP",
    "CSP-Manufacturing-plant",
    "Colour Shift Pigment",
    "Paper Line",
    "Clextral",
    "Schoen",
    "Schoen + Sandt",
    "Sandt",
    "Isravision",
    "Voith",
    "Bivis",
    "Lang",
    "Sheeter",
    "PM 5",
    "PM 6",
    "Security Thread",
    "Fibres",
    "Fibers",
    "BCLP",
    "BCCP",
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
    "ICAO",
    "Electronic Contactless Inlays",
    "e-passport",
    "Development Tender",
    "Refurbishment and Modernization of Coining Presses",
    "Thales",
    "NATIONAL COMPETITIVE BID",
    "Global Tender",
    "CATIONIC UV CURING OVER-PRINT VARNISH",
    "Varnish",
    "Egates",
    "Border Control",
    "Lathe Machine",
    "Giesecke & Devrient",
    "Printing Machine",
    "Reinforced Tear & Water-Resistant Paper",
    "Ghost Image",
    "LSI",
    "Letter Screen Image",
    "Secondary image for passport"
]

# -------------------------
# Email
# -------------------------

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# -------------------------
# Logging
# -------------------------

LOG_DIR = "logs"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    filename=f"{LOG_DIR}/app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)
