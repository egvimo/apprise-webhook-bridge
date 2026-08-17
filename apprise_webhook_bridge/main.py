from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from apprise_webhook_bridge.config import Settings
from apprise_webhook_bridge.metrics import setup_metrics
from apprise_webhook_bridge.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()

    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            connect=2.0,
            read=10.0,
            write=10.0,
            pool=2.0,
        ),
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
        ),
    )

    app.state.settings = settings
    app.state.http_client = http_client

    try:
        yield
    finally:
        await http_client.aclose()


app = FastAPI(title="Apprise Webhook Bridge", lifespan=lifespan)

app.include_router(router=router)
setup_metrics(app)
