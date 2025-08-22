import json
import pathlib
import sys
import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
pytest.importorskip('yaml')

from alertproxy import create_app
from apps.process_alert.process_alert import ProcessAlert


def sample_payload():
    return {
        "status": "firing",
        "commonLabels": {
            "alertname": "TestAlert",
            "overseerID": "ovr",
            "coreAccountID": "acct"
        },
        "commonAnnotations": {
            "summary": "summary",
            "description": "description"
        },
        "alerts": [
            {
                "fingerprint": "abc",
                "startsAt": "2020-01-01T00:00:00Z",
                "labels": {"instance": "localhost", "severity": "critical"}
            }
        ]
    }


def test_severity_from_labels(monkeypatch):
    app = create_app()
    payload = sample_payload()
    monkeypatch.setattr(ProcessAlert, "_is_alert_still_firing", lambda self, fp: True)
    called = {}

    def fake_create(self, url, headers, payload):
        called["url"] = url

    monkeypatch.setattr(ProcessAlert, "_create_core_ticket", fake_create)
    with app.test_request_context('/alert/process', method='POST', json=payload):
        ProcessAlert().post()
    assert "severity=high" in called["url"]


def test_request_id_absent(monkeypatch):
    app = create_app()
    payload = sample_payload()
    monkeypatch.setattr(ProcessAlert, "_is_alert_still_firing", lambda self, fp: True)
    monkeypatch.setattr(ProcessAlert, "_create_core_ticket", lambda self, u, h, p: None)
    with app.test_request_context('/alert/process', method='POST', json=payload):
        ProcessAlert().post()
    assert 'request-id' not in payload['alerts'][0]['labels']


def test_is_alert_still_firing(monkeypatch):
    pa = ProcessAlert()

    class Resp:
        status_code = 200

        def json(self):
            return [{
                'fingerprint': 'abc',
                'status': {'state': 'active'}
            }]

    monkeypatch.setattr('apps.process_alert.process_alert.requests.get', lambda url: Resp())
    assert pa._is_alert_still_firing('abc') is True

    class RespInactive:
        status_code = 200

        def json(self):
            return [{
                'fingerprint': 'abc',
                'status': {'state': 'inactive'}
            }]

    monkeypatch.setattr('apps.process_alert.process_alert.requests.get', lambda url: RespInactive())
    assert pa._is_alert_still_firing('abc') is False
