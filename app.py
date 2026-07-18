from flask import Flask, jsonify
from main import main
from config import logger

app = Flask(__name__)

running = False


@app.route("/")
def home():

    print("=" * 70)
    print("Health Check Request Received")
    print("=" * 70)

    logger.info("Health check endpoint called.")

    return jsonify({
        "status": "SPMCIL Tender Monitor is Running"
    })


@app.route("/run")
def run():

    global running

    print("\n" + "=" * 70)
    print("Tender Monitor API Triggered")
    print("=" * 70)

    if running:

        print("Another scraper instance is already running.")

        logger.warning("Scraper already running.")

        return jsonify({
            "success": False,
            "message": "Scraper is already running."
        }), 409

    try:

        running = True

        print("Starting Tender Monitoring Process...\n")

        logger.info("Starting Tender Monitoring Process.")

        result = main()

        print("\nTender Monitoring Completed Successfully.")

        print("Summary")

        print(f"Total Scraped        : {result.get('total_scraped', 0)}")
        print(f"New Tenders          : {result.get('new_tenders', 0)}")
        print(f"Keyword Matches      : {result.get('matched_tenders', 0)}")

        print("=" * 70)

        logger.info("Tender Monitoring Completed Successfully.")

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception as e:

        print("\nApplication Failed!")
        print(f"Reason : {e}")

        print("=" * 70)

        logger.exception(e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:

        running = False

        print("Scraper Lock Released.")
        print("=" * 70 + "\n")


if __name__ == "__main__":

    print("=" * 70)
    print("Starting Flask Server...")
    print("SPMCIL Tender Monitor API")
    print("Local URL : http://127.0.0.1:5000")
    print("Run API   : http://127.0.0.1:5000/run")
    print("=" * 70)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )