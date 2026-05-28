from mcp.server import transport_security as _ts
from mcp.server.transport_security import TransportSecuritySettings as _TSS
_ts.TransportSecurityMiddleware.__init__ = lambda self, settings=None: setattr(self, "settings", _TSS(enable_dns_rebinding_protection=False))

from mcp.server.fastmcp import FastMCP
from datetime import datetime
import json
import os
import uuid

mcp = FastMCP("approval-mcp")

APPROVALS = {}


@mcp.tool()
def request_approval(action: str, resource: str, requestor: str, justification: str) -> str:
    """Request approval before performing a sensitive action such as sending payment, updating records, or exporting data.
    Returns an approval_id that must be passed to confirm_approval before the action can proceed."""
    approval_id = f"APR-{str(uuid.uuid4())[:8].upper()}"
    record = {
        "approval_id": approval_id,
        "action": action,
        "resource": resource,
        "requestor": requestor,
        "justification": justification,
        "status": "pending",
        "requested_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "resolved_at": None,
    }
    APPROVALS[approval_id] = record
    return json.dumps({
        "approval_id": approval_id,
        "status": "pending",
        "message": f"Approval requested for action '{action}' on resource '{resource}'. Pass approval_id to confirm_approval to proceed.",
    })


@mcp.tool()
def confirm_approval(approval_id: str) -> str:
    """Confirm a pending approval request. Returns granted status and the original action details.
    Must be called before a sensitive downstream action is executed."""
    record = APPROVALS.get(approval_id)
    if not record:
        return json.dumps({"error": f"Approval ID {approval_id} not found."})
    if record["status"] != "pending":
        return json.dumps({"error": f"Approval {approval_id} is already {record['status']}."})
    record["status"] = "granted"
    record["resolved_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return json.dumps({
        "approval_id": approval_id,
        "status": "granted",
        "action": record["action"],
        "resource": record["resource"],
        "message": "Approval granted. You may now proceed with the action.",
    })


@mcp.tool()
def deny_approval(approval_id: str, reason: str) -> str:
    """Deny a pending approval request. The downstream action must not proceed."""
    record = APPROVALS.get(approval_id)
    if not record:
        return json.dumps({"error": f"Approval ID {approval_id} not found."})
    if record["status"] != "pending":
        return json.dumps({"error": f"Approval {approval_id} is already {record['status']}."})
    record["status"] = "denied"
    record["resolved_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    record["denial_reason"] = reason
    return json.dumps({
        "approval_id": approval_id,
        "status": "denied",
        "reason": reason,
        "message": "Approval denied. The action must not proceed.",
    })


@mcp.tool()
def get_approval_status(approval_id: str) -> str:
    """Check the current status of an approval request."""
    record = APPROVALS.get(approval_id)
    if not record:
        return json.dumps({"error": f"Approval ID {approval_id} not found."})
    return json.dumps(record)


@mcp.tool()
def list_pending_approvals() -> str:
    """List all approvals that are currently in pending status."""
    pending = [r for r in APPROVALS.values() if r["status"] == "pending"]
    return json.dumps({"count": len(pending), "approvals": pending})



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
