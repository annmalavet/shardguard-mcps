from mcp.server import transport_security as _ts
from mcp.server.transport_security import TransportSecuritySettings as _TSS
_ts.TransportSecurityMiddleware.__init__ = lambda self, settings=None: setattr(self, "settings", _TSS(enable_dns_rebinding_protection=False))

from mcp.server.fastmcp import FastMCP
from datetime import datetime
import json
import os
import uuid

mcp = FastMCP("audit-log-mcp")

AUDIT_LOG = [
    {
        "id": "log-001",
        "timestamp": "2025-05-20T09:12:34Z",
        "actor": "agent-session-a1b2",
        "action": "get_employee_record",
        "resource": "E003",
        "sensitive_fields_accessed": ["ssn", "salary", "bank_account"],
        "outcome": "success",
    },
    {
        "id": "log-002",
        "timestamp": "2025-05-20T09:13:01Z",
        "actor": "agent-session-a1b2",
        "action": "get_account_record",
        "resource": "ACC003",
        "sensitive_fields_accessed": ["account_number", "routing_number", "credit_score"],
        "outcome": "success",
    },
    {
        "id": "log-003",
        "timestamp": "2025-05-21T11:45:00Z",
        "actor": "agent-session-c3d4",
        "action": "update_employee_record",
        "resource": "E001",
        "sensitive_fields_accessed": ["role"],
        "outcome": "success",
    },
    {
        "id": "log-004",
        "timestamp": "2025-05-22T14:02:19Z",
        "actor": "agent-session-e5f6",
        "action": "get_employee_salary",
        "resource": "E005",
        "sensitive_fields_accessed": ["salary"],
        "outcome": "success",
    },
    {
        "id": "log-005",
        "timestamp": "2025-05-23T08:30:55Z",
        "actor": "agent-session-g7h8",
        "action": "get_transaction_history",
        "resource": "ACC002",
        "sensitive_fields_accessed": ["transactions"],
        "outcome": "success",
    },
]


@mcp.tool()
def append_audit_entry(actor: str, action: str, resource: str, sensitive_fields_accessed: str, outcome: str) -> str:
    """Append a new entry to the audit log. sensitive_fields_accessed should be a comma-separated list of field names."""
    entry = {
        "id": f"log-{str(uuid.uuid4())[:8]}",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor": actor,
        "action": action,
        "resource": resource,
        "sensitive_fields_accessed": [f.strip() for f in sensitive_fields_accessed.split(",")],
        "outcome": outcome,
    }
    AUDIT_LOG.append(entry)
    return json.dumps({"status": "appended", "entry": entry})


@mcp.tool()
def get_audit_log(limit: int = 20) -> str:
    """Get the most recent audit log entries. Defaults to the last 20 entries."""
    entries = AUDIT_LOG[-limit:]
    return json.dumps({"count": len(entries), "entries": entries})


@mcp.tool()
def search_audit_log(query: str) -> str:
    """Search audit log entries by actor, action, or resource."""
    query = query.lower()
    results = [
        entry for entry in AUDIT_LOG
        if query in entry["actor"].lower()
        or query in entry["action"].lower()
        or query in entry["resource"].lower()
    ]
    return json.dumps({"count": len(results), "entries": results})


@mcp.tool()
def get_sensitive_field_access_report() -> str:
    """Return a summary of how many times each sensitive field has been accessed across all log entries."""
    field_counts = {}
    for entry in AUDIT_LOG:
        for field in entry["sensitive_fields_accessed"]:
            field_counts[field] = field_counts.get(field, 0) + 1
    sorted_counts = dict(sorted(field_counts.items(), key=lambda x: x[1], reverse=True))
    return json.dumps({"field_access_counts": sorted_counts})



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
