from typing import Generator

import pytest
from fastapi.testclient import TestClient
from pytest_httpserver import HTTPServer

from apprise_webhook_bridge.main import app


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def apprise_config(client: TestClient, httpserver: HTTPServer) -> None:
    """
    Default autouse fixture that prepares mocks for the Apprise API.
    """
    client.app.state.settings.apprise_api_base_url = (
        f"http://{httpserver.host}:{httpserver.port}"
    )

    httpserver.expect_request("/notify/test").respond_with_json({"success": True})
    httpserver.expect_request("/notify/test-fail").respond_with_json(
        {"error": "Failed"}, status=422
    )
