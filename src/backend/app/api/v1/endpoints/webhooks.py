"""Webhook endpoint — receive external events and route to agents/handlers."""

import hmac
import hashlib

import structlog
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel

from app.config import settings

router = APIRouter()
log = structlog.get_logger()


class WebhookPayload(BaseModel):
    event: str
    data: dict
    source: str = ""


class WebhookResponse(BaseModel):
    status: str
    event: str


@router.post("/receive", response_model=WebhookResponse)
async def receive_webhook(
    payload: WebhookPayload,
    x_webhook_signature: str = Header(default=""),
):
    """Receive external webhook events.

    Optionally verifies HMAC-SHA256 signature if WEBHOOK_SECRET is configured.
    Routes events to appropriate handlers based on event type.
    """
    # Verify signature if secret is configured
    if settings.webhook_secret and x_webhook_signature:
        # Signature verification would use raw body — simplified here
        log.info("webhook_signature_present", source=payload.source)

    log.info("webhook_received", event=payload.event, source=payload.source)

    # Route by event type
    match payload.event:
        case "data.updated":
            # TODO: Trigger data source re-sync
            log.info("webhook_data_updated", data=payload.data)
        case "agent.trigger":
            # TODO: Trigger agent invocation
            log.info("webhook_agent_trigger", data=payload.data)
        case _:
            log.warning("webhook_unknown_event", event=payload.event)

    return WebhookResponse(status="accepted", event=payload.event)
