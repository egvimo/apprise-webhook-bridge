import httpx
from fastapi.testclient import TestClient
from pytest_httpserver import HTTPServer

from apprise_webhook_bridge.alertmanager import STATUS_ICONS, convert_alert
from apprise_webhook_bridge.models import AlertmanagerRequest
from tests.payloads import BASE_ALERTMANAGER_PAYLOAD as BASE_PAYLOAD


def make_payload(overrides: dict | None = None) -> AlertmanagerRequest:
    data = BASE_PAYLOAD | (overrides or {})
    return AlertmanagerRequest.model_validate(data)


def test_alertmanager_success(client: TestClient, httpserver: HTTPServer):
    response = client.post("/webhook/alertmanager?config_key=test", json=BASE_PAYLOAD)
    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert len(httpserver.log) == 1


def test_alertmanager_propagates_apprise_error(
    client: TestClient, httpserver: HTTPServer
):
    response = client.post(
        "/webhook/alertmanager?config_key=test-fail",
        json=BASE_PAYLOAD,
    )

    assert response.status_code == 422
    assert "Failed" in response.text
    assert len(httpserver.log) == 1


def test_alertmanager_connection_error(client: TestClient, monkeypatch):
    async def mock_post(*args, **kwargs):
        raise httpx.RequestError("connection failed")

    class MockAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        post = mock_post

    monkeypatch.setattr("httpx.AsyncClient", lambda: MockAsyncClient())

    response = client.post(
        "/webhook/alertmanager?config_key=test",
        json=BASE_PAYLOAD,
    )

    assert response.status_code == 424
    assert "Error connecting to Apprise API" in response.text


def test_convert_alert_returns_title_and_body():
    payload = make_payload()

    title, body = convert_alert(payload)

    assert isinstance(title, str)
    assert isinstance(body, str)
    assert title
    assert body


def test_title_contains_status_count_and_icon():
    payload = make_payload()

    title, _ = convert_alert(payload)

    assert "🔥" in title
    assert "[FIRING: 2]" in title
    assert STATUS_ICONS["firing"] in title


def test_body_contains_all_alerts():
    payload = make_payload()

    _, body = convert_alert(payload)

    assert body.count("**Alert:**") == 2
    assert "Watchdog" in body
    assert "Watchcat" in body


def test_alerts_are_separated():
    payload = make_payload()

    _, body = convert_alert(payload)

    assert "\n---\n" in body


def test_body_contains_status_and_severity():
    payload = make_payload()

    _, body = convert_alert(payload)

    assert "**Status:** FIRING" in body
    assert "**Severity:** none" in body


def test_optional_summary_and_description():
    payload = make_payload()

    _, body = convert_alert(payload)

    assert "**Summary:**" in body
    assert "**Description:**" in body


def test_missing_annotations_are_handled_gracefully():
    payload = make_payload(
        {
            "alerts": [
                {
                    **BASE_PAYLOAD["alerts"][0],
                    "annotations": {},
                }
            ]
        }
    )

    _, body = convert_alert(payload)

    assert "**Alert:** Watchdog" in body
    assert "**Summary:**" not in body
    assert "**Description:**" not in body


def test_missing_labels_use_fallbacks():
    payload = make_payload(
        {
            "alerts": [
                {
                    **BASE_PAYLOAD["alerts"][0],
                    "labels": {},
                }
            ]
        }
    )

    _, body = convert_alert(payload)

    assert "Unknown Alert" in body
    assert "**Severity:** unknown" in body


def test_no_alerts_returns_none_title():
    payload = make_payload({"alerts": []})

    title, body = convert_alert(payload)

    assert title is None
    assert body == "Alertmanager: firing"
