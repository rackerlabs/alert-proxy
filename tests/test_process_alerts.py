#   ___  _           _  ______
#  / _ \| |         | | | ___ \
# / /_\ \ | ___ _ __| |_| |_/ / __ _____  ___   _
# |  _  | |/ _ \ '__| __|  __/ '__/ _ \ \/ / | | |
# | | | | |  __/ |  | |_| |  | | | (_) >  <| |_| |
# \_| |_/_|\___|_|   \__\_|  |_|  \___/_/\_\\__, |
#                    Alert-Proxy             __/ |
#                                           |___/
import json
import pathlib
import sys
import pytest

# Add the 'src' directory to the Python path to allow imports from it
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

# Import the necessary components
from alertproxy import create_app
from apps.process_alert.process_alert import ProcessAlert
from config.config import Config, settings


def sample_payload():
    return {
        "status": "firing",
        "commonLabels": {
            "alertname": "TestAlert",
            "overseerID": "ovr",
            "coreAccountID": "acct",
        },
        "commonAnnotations": {"summary": "summary", "description": "description"},
        "alerts": [
            {
                "fingerprint": "abc",
                "startsAt": "2020-01-01T00:00:00Z",
                "labels": {"instance": "localhost", "severity": "critical"},
            }
        ],
    }


@pytest.fixture(autouse=True)
def setup_config_and_app(monkeypatch):
    """
    A fixture that sets up the configuration and Flask app for tests.
    """
    # Construct the path to the real sample file
    config_file_path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "src"
        / "config"
        / "config.yaml.sample"
    )

    # Set environment variables for substitution
    monkeypatch.setenv("CORE_ACCOUNT_NUMBER", "123456")
    monkeypatch.setenv("OVERSEER_CORE_DEVICE_ID", "654321")
    monkeypatch.setenv("ACCOUNT_SERVICE_TOKEN", "1111-2222-3333-4444")
    monkeypatch.setenv("ALERT_MANAGER_BASE_URL", "https://this.is.a.url")

    # Reset the Config singleton to a clean state
    Config._instance = None
    Config._initialized = False

    # Create a new Config instance and load the sample file
    new_settings = Config(str(config_file_path))

    # Monkeypatch the global settings object to point to the new instance
    monkeypatch.setattr("config.config.settings", new_settings)

    # Create and return the Flask app instance
    yield create_app()


def test_severity_from_labels(monkeypatch, setup_config_and_app):
    app = setup_config_and_app
    payload = sample_payload()
    monkeypatch.setattr(ProcessAlert, "_is_alert_still_firing", lambda self, fp: True)
    called = {}

    def fake_create(self, url, headers, payload):
        called["url"] = url

    monkeypatch.setattr(ProcessAlert, "_create_core_ticket", fake_create)
    with app.test_request_context("/alert/process", method="POST", json=payload):
        ProcessAlert().post()
    assert "severity=high" in called["url"]


def test_request_id_absent(monkeypatch, setup_config_and_app):
    app = setup_config_and_app
    payload = sample_payload()
    monkeypatch.setattr(ProcessAlert, "_is_alert_still_firing", lambda self, fp: True)
    monkeypatch.setattr(ProcessAlert, "_create_core_ticket", lambda self, u, h, p: None)
    with app.test_request_context("/alert/process", method="POST", json=payload):
        ProcessAlert().post()
    assert "request-id" not in payload["alerts"][0]["labels"]


def test_is_alert_still_firing(monkeypatch):
    pa = ProcessAlert()

    class Resp:
        status_code = 200

        def json(self):
            return [{"fingerprint": "abc", "status": {"state": "active"}}]

    monkeypatch.setattr(
        "apps.process_alert.process_alert.requests.get", lambda url: Resp()
    )
    assert pa._is_alert_still_firing("abc") is True

    class RespInactive:
        status_code = 200

        def json(self):
            return [{"fingerprint": "abc", "status": {"state": "inactive"}}]

    monkeypatch.setattr(
        "apps.process_alert.process_alert.requests.get", lambda url: RespInactive()
    )
    assert pa._is_alert_still_firing("abc") is False
