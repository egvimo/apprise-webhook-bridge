from typing import Any, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "OK"


class NotifyResponse(BaseModel):
    success: Optional[bool]


class AlertmanagerAlert(BaseModel):
    status: str
    labels: dict[str, Any] = Field(default_factory=dict)
    annotations: dict[str, Any] = Field(default_factory=dict)


class AlertmanagerRequest(BaseModel):
    status: str
    alerts: list[AlertmanagerAlert]
    groupLabels: dict[str, Any] = Field(default_factory=dict)
    commonLabels: dict[str, Any] = Field(default_factory=dict)
    commonAnnotations: dict[str, Any] = Field(default_factory=dict)
