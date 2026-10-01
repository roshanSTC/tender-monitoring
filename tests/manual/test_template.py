from services.template_service import TemplateService

html = TemplateService.render(
    "emails/corrigendum.html",
    user_name="Roshan",
    tender_number="TDR-001",
    tender_title="Supply of Equipment",
    source="SPMCIL",
    corrigendum_no="Corrigendum-1",
    old_closing_date="10-Aug-2026",
    new_closing_date="20-Aug-2026",
    change_summary="Closing date extended by 10 days.",
    corrigendum_url="https://example.com"
)

with open("test_email.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Generated test_email.html")