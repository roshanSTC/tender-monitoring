

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

    if running:
        return jsonify({
            "success": False,
            "message": "Scraper is already running."
        }), 409

    try:
        running = True
        logger.info("Tender monitoring started via API")

        result = main()

        logger.info("Tender monitoring completed")

        return jsonify(result)

    except Exception as e:
        logger.exception(e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        running = False


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