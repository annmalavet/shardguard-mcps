from mcp.server import transport_security as _ts
from mcp.server.transport_security import TransportSecuritySettings as _TSS
_ts.TransportSecurityMiddleware.__init__ = lambda self, settings=None: setattr(self, "settings", _TSS(enable_dns_rebinding_protection=False))

from mcp.server.fastmcp import FastMCP
from datetime import datetime
import json
import os
import uuid

mcp = FastMCP("notification-mcp")

SENT_NOTIFICATIONS = []

TEMPLATES = {
    "payroll": "Hi {name}, your payroll of {amount} has been deposited to your account.",
    "alert": "Security alert for {name}: {message}",
    "reminder": "Hi {name}, this is a reminder: {message}",
    "welcome": "Welcome {name}, your account has been created successfully.",
}


@mcp.tool()
def send_notification(recipient_email: str, subject: str, body: str) -> str:
    """Send a notification message to a recipient by email. Logs the full message content."""
    record = {
        "id": f"notif-{str(uuid.uuid4())[:8]}",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "recipient_email": recipient_email,
        "subject": subject,
        "body": body,
        "status": "sent",
    }
    SENT_NOTIFICATIONS.append(record)
    return json.dumps({"status": "sent", "notification_id": record["id"], "recipient": recipient_email})


@mcp.tool()
def send_templated_notification(recipient_email: str, template_name: str, template_vars: str) -> str:
    """Send a notification using a named template. template_vars should be a JSON string of key-value pairs.
    Available templates: payroll, alert, reminder, welcome."""
    template = TEMPLATES.get(template_name)
    if not template:
        return json.dumps({"error": f"Template '{template_name}' not found. Available: {list(TEMPLATES.keys())}"})
    try:
        vars_dict = json.loads(template_vars)
    except json.JSONDecodeError:
        return json.dumps({"error": "template_vars must be a valid JSON string."})
    try:
        body = template.format(**vars_dict)
    except KeyError as e:
        return json.dumps({"error": f"Missing required template variable: {e}"})
    record = {
        "id": f"notif-{str(uuid.uuid4())[:8]}",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "recipient_email": recipient_email,
        "template": template_name,
        "body": body,
        "status": "sent",
    }
    SENT_NOTIFICATIONS.append(record)
    return json.dumps({"status": "sent", "notification_id": record["id"], "recipient": recipient_email, "body": body})


@mcp.tool()
def get_sent_notifications(limit: int = 20) -> str:
    """Get the most recently sent notifications including full message content."""
    entries = SENT_NOTIFICATIONS[-limit:]
    return json.dumps({"count": len(entries), "notifications": entries})


@mcp.tool()
def search_sent_notifications(recipient_email: str) -> str:
    """Search sent notifications by recipient email address."""
    results = [n for n in SENT_NOTIFICATIONS if recipient_email.lower() in n["recipient_email"].lower()]
    return json.dumps({"count": len(results), "notifications": results})


@mcp.tool()
def list_templates() -> str:
    """List all available notification templates and their formats."""
    return json.dumps({"templates": TEMPLATES})



if __name__ == "__main__":
    import uvicorn

    _inner = mcp.streamable_http_app()

    async def _app(scope, receive, send):
        if scope["type"] == "http":
            scope = dict(scope)
            scope["headers"] = [
                (k, v) for k, v in scope["headers"] if k.lower() != b"host"
            ] + [(b"host", b"localhost")]
        await _inner(scope, receive, send)

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(_app, host="0.0.0.0", port=port)
