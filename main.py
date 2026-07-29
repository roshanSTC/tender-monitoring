"""
main.py

Main entry point for the SPMCIL Tender Monitoring System.
"""


from services.active_tenders import count_active_tenders
from scraper.scraper import TenderScraper
from services.compare import TenderComparer
from services.filter import TenderFilter
from notifications.mailer import TenderMailer
from storage.google_sheet import GoogleSheet
from config import logger, TENDER_SITES
sheet = GoogleSheet()


def main():

    print("=" * 70)
    print("        Tender Monitoring System")
    print("=" * 70)

    logger.info("Application Started")

    scraper = TenderScraper()
    mailer = TenderMailer()
    filter_obj = TenderFilter()

    try:

        # ---------------------------------------------------
        # Scrape all websites
        # ---------------------------------------------------

        all_tenders = []

        print("\nScraping Websites...\n")
        
        
        for site in TENDER_SITES:

            try:

                print(f"Scraping : {site['name']}")

                tenders = scraper.scrape(site)

                print(f"Found {len(tenders)} tenders")

                logger.info(
                    f"{site['name']} -> {len(tenders)} tenders scraped"
                )
                
                # Debug only for BRBNMPL
                if site["name"] == "BRBNMPL":

                    seen = set()

                    for tender in tenders:

                        key = f"{tender['Source']}|{tender['Tender Number']}"

                        if key in seen:
                            print(f"DUPLICATE FROM PARSER: {key}")

                        seen.add(key)

                all_tenders.extend(tenders)

            except Exception as e:

                logger.exception(
                    f"Failed to scrape {site['name']} : {e}"
                )

                print(f"Failed : {site['name']}")
                print(f"Error Type : {type(e).__name__}")
                print(f"Error      : {e}")

        print("\n---------------------------------------")
        print(f"Total Scraped : {len(all_tenders)}")
        print("---------------------------------------")

        # ---------------------------------------------------
        # Create Excel if not exists
        # ---------------------------------------------------

        sheet.create_sheet()

        # ---------------------------------------------------
        # Existing tenders
        # ---------------------------------------------------

        existing = sheet.get_existing_tenders()

        print(f"Existing Tenders : {len(existing)}")

        # ---------------------------------------------------
        # Compare
        # ---------------------------------------------------

        comparer = TenderComparer(existing)

        new_tenders = comparer.get_new_tenders(all_tenders)

        print(f"New Tenders : {len(new_tenders)}")

        

        # ---------------------------------------------------
        # Filter
        # ---------------------------------------------------

        filtered_tenders = filter_obj.filter_by_title(new_tenders)

        print(
            f"Keyword Matched Tenders : {len(filtered_tenders)}"
        )
        
        
        # ---------------------------------------------------
        # Save new tenders
        # ---------------------------------------------------

        if new_tenders:

            sheet.save_to_sheet(new_tenders, existing)

            print("Excel updated successfully.")

        else:

            print("No new tenders found.")
            
            
            
        #active tenders-------------------- 
        
        active_tenders, expired_tenders = count_active_tenders(
                all_tenders
            )   
        # symmary---------------------------
        
        summary = {
                "status": "SUCCESS",
                "total_websites": len(TENDER_SITES),
                "total_scraped": len(all_tenders),
                "active_tenders": active_tenders,
                "existing_tenders": len(existing),
                "new_tenders": len(new_tenders),
                "keyword_matches": len(filtered_tenders)
            }


        # ---------------------------------------------------
        # Email
        # ---------------------------------------------------

        if filtered_tenders:

            mailer.send_email(filtered_tenders, summary)

            print("Email sent successfully.")

        else:

            mailer.send_health_report(summary)

            print("Health report sent successfully.")

        logger.info("Application Finished Successfully")

        print("\nCompleted Successfully.")

        return {
            "success": True,
            "total_scraped": len(all_tenders),
            "new_tenders": len(new_tenders),
            "matched_tenders": len(filtered_tenders)
        }

    except Exception as e:

        logger.exception(e)

        print(f"\nApplication Failed : {e}")

        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    main()