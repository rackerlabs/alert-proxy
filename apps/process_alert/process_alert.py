#   ___  _           _  ______
#  / _ \| |         | | | ___ \
# / /_\ \ | ___ _ __| |_| |_/ / __ _____  ___   _
# |  _  | |/ _ \ '__| __|  __/ '__/ _ \ \/ / | | |
# | | | | |  __/ |  | |_| |  | | | (_) >  <| |_| |
# \_| |_/_|\___|_|   \__\_|  |_|  \___/_/\_\\__, |
#                    Alert-Proxy             __/ |
#                                           |___/
from flask.views import MethodView
from flask import Blueprint, request, jsonify, current_app, has_request_context
from config.config import AlertProxyConfig
import requests
import json
from apps.process_alert import process_alert_bp


class ProcessAlert(MethodView):
    def _is_alert_still_firing(self, fingerprint=None):
        """
        Query Alert Manager API by fingerprint and confirm status is firing
        Args:
            fingerprint (str): Alert fingercurrent_app.logger.debug to filter on
        """
        alert_status = None
        is_firing = False

        response = requests.get(AlertProxyConfig.AM_V2_BASE_URL)

        if response.status_code == 200:
            alerts = response.json()
            current_app.logger.debug(f"matching_alert: { alerts }")
            if alerts:
                for alert in alerts:
                    alert_status=alert.get('status')
            else:
                current_app.logger.debug(f"No alerts found with fingercurrent_app.logger.debug: { fingercurrent_app.logger.debug }")
        else:
            current_app.logger.debug(f"Failed to retrieve alerts. Status code: {response.status_code}")

        if alert_status == 'firing':
            is_firing = True
        return is_firing

    def _create_core_ticket(self, url=None, headers=None, payload=None):
        """
        Create a core ticket with payload pulled form the Alert

        Args:
            payload (json): Payload used when posting against the Watchman API
        """
        response = None

        try:
            response = requests.post(url=url, headers=headers, json=payload)
            response.raise_for_status()
            current_app.logger.info("Post to watchman api was successful.")
        except requests.exceptions.HTTPError as e:
            current_app.logger.error(f"Request failed: {e}")

        return response

    def get(self):
        current_app.logger.info(f"This is a request")
        return_payload = {"status": "success", "message": "This is a JSON message!"}
        return jsonify(return_payload)        

    def post(self):
        """
        HTTP Post to accept Alertmanager Alert
        """
        current_app.logger.debug(f"Begin alert processing via POST")
        if has_request_context():
            request_id = request.environ.get("HTTP_X_REQUEST_ID")

        alert_data = request.get_json(silent=True)
        if not alert_data:
            current_app.logger.error(f"Invalid or missing json payload")
            return jsonify({"message": "Invalid or missing JSON payload"}), 400

        current_app.logger.debug(f"Value of post from watchman: { alert_data }")
##        a_status = "ALARM" if alert_data['status'] == "firing" else "OK" if alert_data['status'] == "resolved" else "OK"
##        a_subject = alert_data['commonAnnotations']['summary']
##        a_description = alert_data['commonAnnotations']['description']
##        a_coreDeviceID = alert_data['commonLabels']['coreDeviceID']
##        a_coreAccountID = alert_data['commonLabels']['coreAccountID']
##        a_alertURL = "alert_data['generatorURL']"
##        a_secret = AlertProxyConfig.ACCOUNT_SECRET
##
##        current_app.logger.debug(f"ALERT_DATA: { alert_data }")
##
##        alerts = alert_data.get('alerts', [])
##        for alert in alerts:
##            alert['labels']['request-id'] = request_id
##            a_fingercurrent_app.logger.debug = alert.get('fingercurrent_app.logger.debug','UNKNOWN')
##            current_app.logger.debug(f"value of a_fingercurrent_app.logger.debug: { a_fingercurrent_app.logger.debug }")
##            if AlertProxyConifg.ALERT_VERIFICATION:
##                if self._is_alert_still_firing(a_fingercurrent_app.logger.debug):
##                    current_app.logger.debug(f"Alert with fingercurrent_app.logger.debug: { a_fingercurrent_app.logger.debug } is still firing: proceeding to ticket creation")
##                else:
##                    return jsonify({"message": "Alert no longer firing, skipping ticket creation."}), 200
##            current_app.logger.info(f"Formatting alert for watchman ingestion")
##            w_url = f"{ watchman_endpoint }:{ a_coreAccountID }/webbook/platformservices?secret={ a_secret }"
##            w_headers = {
##                    "Accept": "application/json",
##                    "Content-Type": "application/json"
##            }
##            w_payload = {
##                "subject": f"PROXY-{ a_subject }",
##                "body": f"Severity: Standard\nInstance: { alert.get('labels', {}).get('instance','UNKNOWN') }\ncoreDeviceID: { a_coreDeviceID }\ncoreAccountID: { a_coreAccountID }\nDescription: { a_description }\nStarted at: { alert.get('startsAt','UNKNOWN') }\nalertURL: { a_alertURL }\nNOTE: NO ACTION NEEDED, THIS IS FOR ALERTMANGER->CORE Ticket creation testing.  (chris.breu)",
##                "privateComment": "\n".join([f"{x}:{v}" for x, v in alert.get('labels').items()]),
##                "alarmState": a_status,
##                "threadId": f"platformservices-{ a_coreAccountID }-brew",
##                "sender": ""
##            }
##            # post the payload against watchman
#            try:
#                current_app.logger.debug(f"Payload: {w_payload}")
#                response = self._create_core_ticket(w_url, w_headers, w_payload)
#                return jsonify({"message": "Alert received successfully"}), 200
#            except Exception as e:
#                return jsonify({"error": f"Invalid JSON detected: {str(e)}"}), 400


process_alert_bp.add_url_rule('/process', view_func=ProcessAlert.as_view('alert_api'))
