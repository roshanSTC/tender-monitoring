from datetime import datetime

from sqlalchemy.dialects.postgresql import insert

from models import Tender
from utils.normalizer import TenderNormalizer


# ---------------------------------------------------------
# Existing Tenders
# ---------------------------------------------------------

def get_existing_tenders(db):
    """
    Returns all tenders indexed by:

        Source|Tender Number
    """

    tenders = db.query(Tender).all()

    existing = {}

    for tender in tenders:

        key = f"{tender.source}|{tender.tender_number}"

        existing[key] = tender

    return existing


# ---------------------------------------------------------
# Bulk Insert
# ---------------------------------------------------------

def save_new_tenders(
    db,
    scraped_tenders,
):
    """
    Bulk insert only NEW tenders.

    Uses PostgreSQL ON CONFLICT DO NOTHING.
    """

    if not scraped_tenders:
        return []

    rows = []

    for data in scraped_tenders:

        source = (
            data.get("Source") or ""
        ).strip()

        tender_number = (
            data.get("Tender Number") or ""
        ).strip()

        if not source or not tender_number:
            continue

        rows.append({

            "source": source,

            "tender_number": tender_number,

            "title": data.get("Tender Title"),

            "unit_name": data.get("Unit Name"),

            "publishing_date": data.get("Publishing Date"),

            "closing_date": data.get("Closing Date"),

            "tender": data.get("Tender"),

            "tender_url": data.get("Tender URL"),

            "corrigendum": data.get("Corrigendum"),

            "corrigendum_url": data.get("Corrigendum URL"),

            "created_at": datetime.utcnow(),

            "updated_at": datetime.utcnow(),

        })

    if not rows:
        return []

    # ----------------------------------------
    # Remove duplicates from current scrape
    # ----------------------------------------

    unique_rows = {}

    for row in rows:

        key = (
            row["source"],
            row["tender_number"],
        )

        if key not in unique_rows:
            unique_rows[key] = row

    rows = list(unique_rows.values())

    stmt = insert(Tender).values(rows)

    stmt = stmt.on_conflict_do_nothing(
        constraint="uq_tender_source_number"
    )

    stmt = stmt.returning(

        Tender.id,

        Tender.source,

        Tender.tender_number,

        Tender.title,

        Tender.unit_name,

        Tender.publishing_date,

        Tender.closing_date,

        Tender.tender,

        Tender.tender_url,

        Tender.corrigendum,

        Tender.corrigendum_url,

    )

    result = db.execute(stmt)

    inserted_rows = result.mappings().all()

    new_tenders = []

    for row in inserted_rows:

        new_tenders.append({

            "id": row["id"],

            "Source": row["source"],

            "Tender Number": row["tender_number"],

            "Tender Title": row["title"],

            "Unit Name": row["unit_name"],

            "Publishing Date": row["publishing_date"],

            "Closing Date": row["closing_date"],

            "Tender": row["tender"],

            "Tender URL": row["tender_url"],

            "Corrigendum": row["corrigendum"],

            "Corrigendum URL": row["corrigendum_url"],

        })

    return new_tenders


# ---------------------------------------------------------
# Update Existing Tender
# ---------------------------------------------------------

def update_tender(
    db,
    tender,
    scraped,
):
    """
    Update an existing tender.

    TenderComparer already determined that
    something changed.
    """

    tender.title = (
        scraped.get("Tender Title")
        or tender.title
    )

    tender.unit_name = (
        scraped.get("Unit Name")
        or tender.unit_name
    )

    tender.publishing_date = TenderNormalizer.date((
        scraped.get("Publishing Date")
        or tender.publishing_date
    ))

    tender.closing_date = TenderNormalizer.date((
        scraped.get("Closing Date")
        or tender.closing_date
    ))

    tender.tender = (
        scraped.get("Tender")
        or tender.tender
    )

    tender.tender_url = (
        scraped.get("Tender URL")
        or tender.tender_url
    )

    tender.corrigendum = (
        scraped.get("Corrigendum")
        or tender.corrigendum
    )

    tender.corrigendum_url = (
        scraped.get("Corrigendum URL")
        or tender.corrigendum_url
    )

    tender.updated_at = datetime.utcnow()

    return tender