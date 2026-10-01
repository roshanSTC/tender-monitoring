

from flask import Flask, jsonify, redirect, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_swagger_ui import get_swaggerui_blueprint
from main import main
from config import logger, JWT_SECRET_KEY, CORS_ORIGINS
from database.connection import test_connection
from routes.notifications import notifications_bp
from routes.preferences import preferences_bp
from auth.routes import auth_bp
from routes.tenders import tenders_bp
from routes.dashboard import dashboard_bp
from routes.admin_users import admin_users_bp
from routes.admin_dashboard import admin_dashboard_bp
from routes.corrigendums import corrigendum_bp

app = Flask(__name__)

# Production CORS
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": CORS_ORIGINS
        }
    }
)

# JWT configuration from environment
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY

jwt = JWTManager(app)


@jwt.unauthorized_loader
def unauthorized_callback(callback):
    return jsonify({
        "success": False,
        "message": "Authorization header missing or invalid. Please log in."
    }), 401


@jwt.invalid_token_loader
def invalid_token_callback(callback):
    return jsonify({
        "success": False,
        "message": "Invalid JWT token."
    }), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "success": False,
        "message": "JWT token has expired. Please log in again."
    }), 401

# Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(preferences_bp)
app.register_blueprint(tenders_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(admin_users_bp)
app.register_blueprint(admin_dashboard_bp)
app.register_blueprint(corrigendum_bp)

# ============================================================
# SWAGGER UI CONFIGURATION
# ============================================================
SWAGGER_URL = "/docs"
API_URL = "/swagger.json"

swaggerui_bp = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "app_name": "Tender Monitoring System API",
        "persistAuthorization": True,
        "docExpansion": "list",
    },
)
app.register_blueprint(swaggerui_bp, url_prefix=SWAGGER_URL)


@app.route("/swagger")
def swagger_redirect():
    """Redirect /swagger to /docs for convenience."""
    return redirect("/docs", code=302)


@app.route("/swagger.json")
def swagger_spec():
    """Serve OpenAPI / Swagger JSON specification."""
    return send_from_directory("static", "swagger.json")


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
        
        
@app.route("/api/health/db")
def database_health():

    connected = test_connection()

    if connected:

        return jsonify({
            "status": "success",
            "database": "connected"
        })

    return jsonify({
        "status": "error",
        "database": "disconnected"
    }), 500


# ============================================================
# GLOBAL ERROR HANDLERS (Standard JSON responses)
# ============================================================

@app.errorhandler(400)
def handle_bad_request(e):
    return jsonify({
        "success": False,
        "message": "Bad request.",
        "error": str(e)
    }), 400


@app.errorhandler(404)
def handle_not_found(e):
    return jsonify({
        "success": False,
        "message": "The requested resource was not found."
    }), 404


@app.errorhandler(405)
def handle_method_not_allowed(e):
    return jsonify({
        "success": False,
        "message": "HTTP method not allowed for this route."
    }), 405


@app.errorhandler(500)
def handle_internal_server_error(e):
    logger.exception(f"Unhandled 500 Server Error: {e}")
    return jsonify({
        "success": False,
        "message": "Internal server error occurred."
    }), 500


if __name__ == "__main__":

    print("=" * 70)
    print("Starting Flask Server...")
    print("SPMCIL Tender Monitor API")
    print("Local URL  : http://127.0.0.1:5000")
    print("Swagger UI : http://127.0.0.1:5000/docs")
    print("Run API    : http://127.0.0.1:5000/run")
    print("=" * 70)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )