from typing import Annotated, Optional

import httpx
from fastapi import APIRouter, Body, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from apprise_webhook_bridge.alertmanager import convert_alert
from apprise_webhook_bridge.config import Settings
from apprise_webhook_bridge.logging import logger
from apprise_webhook_bridge.models import (
    AlertmanagerRequest,
    HealthResponse,
)

router = APIRouter()


@router.get(
    "/health",
    tags=["health"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthResponse,
)
async def get_health():
    return HealthResponse()


@router.post(
    "/webhook/alertmanager",
    tags=["alertmanager"],
    summary="Alertmanager Webhook",
    response_description="Pass-through response from Apprise API",
)
async def post_alertmanager(
    config_key: Annotated[str, Query(...)],
    tag: Annotated[Optional[str], Query()] = None,
    request: Request = None,
    alertmanager_request: Annotated[AlertmanagerRequest, Body()] = None,
):
    """
    Accept Alertmanager webhook notifications and forward them to Apprise API.

    This endpoint is designed to be used as a webhook receiver in Alertmanager.
    It converts Alertmanager alert payloads into notifications and sends them
    using the configured Apprise API server.

    Query Parameters:
        config_key: The Apprise configuration key to use
        tag: Optional tag to use for notifications
    """
    settings: Settings = request.app.state.settings
    title, body = convert_alert(alertmanager_request)

    payload = {"body": body, "title": title}
    if tag:
        payload["tag"] = tag

    async with httpx.AsyncClient() as client:
        try:
            upstream = await client.post(
                f"{settings.apprise_api_base_url}/notify/{config_key}",
                json=payload,
                headers={"Accept": "application/json"},
            )

            try:
                content = upstream.json()
            except ValueError:
                logger.error(
                    "Upstream returned non-JSON: %s",
                    upstream.text,
                )
                raise HTTPException(
                    status_code=502,
                    detail="Invalid JSON response from upstream service",
                ) from ValueError

            logger.info(
                "Alert forwarded",
                extra={
                    "config_key": config_key,
                    "status_code": upstream.status_code,
                    "has_error": bool(content.get("error"))
                    if isinstance(content, dict)
                    else None,
                },
            )

            return JSONResponse(content=content, status_code=upstream.status_code)
        except httpx.RequestError as e:
            msg = f"Error connecting to Apprise API: {e}"
            logger.error(msg)
            raise HTTPException(status_code=424, detail=msg) from e
