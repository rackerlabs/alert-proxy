#   ___  _           _  ______
#  / _ \| |         | | | ___ \
# / /_\ \ | ___ _ __| |_| |_/ / __ _____  ___   _
# |  _  | |/ _ \ '__| __|  __/ '__/ _ \ \/ / | | |
# | | | | | __/ |  | |_| |  | | | (_) >  <| |_| |
# \_| |_/_|\___|_|   \__\_|  |_|  \___/_/\_\\__, |
#                    Alert-Proxy             __/ |
#                                           |___/
from flask import Flask, jsonify
from flask_request_id_header.middleware import RequestID
from config.logger import AlertProxyLogger
from config.config import settings

def create_app():
    # create the app from config.py
    app = Flask(__name__)
    app.config['REQUEST_ID_UNIQUE_VALUE_PREFIX'] = 'PXY-'

    # configure the logger
    app_logger_instance = AlertProxyLogger(app)

    # add request-id to all calls
    RequestID(app)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def catch_all(path):
        return jsonify({"message": f"Request revieced on unconfiguered endpoint"}), 202

    # Register process_alert blueprint with /alert/process
    from apps.process_alert import process_alert_bp
    app.register_blueprint(process_alert_bp)
    app.logger.info(f"Blueprint added: { process_alert_bp }")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=settings.app_debug)
