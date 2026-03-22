from contextlib import asynccontextmanager

from fastapi import FastAPI

from apprise_webhook_bridge.config import Settings
from apprise_webhook_bridge.metrics import setup_metrics
from apprise_webhook_bridge.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    app.state.settings = settings
    yield


app = FastAPI(title="Apprise Webhook Bridge", lifespan=lifespan)
app.include_router(router=router)
setup_metrics(app)
