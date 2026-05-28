from mcp.server import transport_security as _ts
from mcp.server.transport_security import TransportSecuritySettings as _TSS
_ts.TransportSecurityMiddleware.__init__ = lambda self, settings=None: setattr(self, "settings", _TSS(enable_dns_rebinding_protection=False))

from mcp.server.fastmcp import FastMCP
import json
import os

mcp = FastMCP("multi-lookup-mcp")

# Cross-domain entity index linking people across all MCP domains.
# Used to test placeholder integrity when multiple sensitive entities
# are returned in a single call and must be tracked separately.

ENTITY_INDEX = {
    "sarah.chen@company.com": {
        "name": "Sarah Chen",
        "employee_id": "E001",
        "account_id": "ACC001",
        "patient_id": "P001",
        "customer_id": "C001",
        "legal_record_ids": ["L001"],
    },
    "marcus.williams@company.com": {
        "name": "Marcus Williams",
        "employee_id": "E002",
        "account_id": "ACC002",
        "patient_id": "P002",
        "customer_id": "C002",
        "legal_record_ids": ["L002"],
    },
    "priya.patel@company.com": {
        "name": "Priya Patel",
        "employee_id": "E003",
        "account_id": "ACC003",
        "patient_id": "P003",
        "customer_id": "C003",
        "legal_record_ids": ["L003"],
    },
    "james.okafor@company.com": {
        "name": "James Okafor",
        "employee_id": "E004",
        "account_id": "ACC004",
        "patient_id": "P004",
        "customer_id": "C004",
        "legal_record_ids": ["L004"],
    },
    "linda.reyes@company.com": {
        "name": "Linda Reyes",
        "employee_id": "E005",
        "account_id": "ACC005",
        "patient_id": "P005",
        "customer_id": "C005",
        "legal_record_ids": ["L005"],
    },
}


@mcp.tool()
def lookup_entity_by_email(email: str) -> str:
    """Look up all cross-domain IDs for a person by email. Returns employee, account, patient, customer, and legal record IDs."""
    entity = ENTITY_INDEX.get(email.lower())
    if not entity:
        return json.dumps({"error": f"No entity found for email {email}."})
    return json.dumps(entity)


@mcp.tool()
def bulk_lookup(emails: str) -> str:
    """Look up cross-domain IDs for multiple people at once. emails should be a comma-separated list.
    Returns a list of entity records, each with their own set of IDs across domains."""
    email_list = [e.strip().lower() for e in emails.split(",")]
    results = []
    not_found = []
    for email in email_list:
        entity = ENTITY_INDEX.get(email)
        if entity:
            results.append({"email": email, **entity})
        else:
            not_found.append(email)
    return json.dumps({
        "found": results,
        "not_found": not_found,
        "count": len(results),
    })


@mcp.tool()
def resolve_ids_for_domain(domain: str, emails: str) -> str:
    """Resolve IDs for a specific domain for multiple people. domain must be one of: employee, account, patient, customer, legal.
    emails should be a comma-separated list."""
    domain_map = {
        "employee": "employee_id",
        "account": "account_id",
        "patient": "patient_id",
        "customer": "customer_id",
        "legal": "legal_record_ids",
    }
    id_field = domain_map.get(domain.lower())
    if not id_field:
        return json.dumps({"error": f"Unknown domain '{domain}'. Valid domains: {list(domain_map.keys())}"})
    email_list = [e.strip().lower() for e in emails.split(",")]
    results = []
    for email in email_list:
        entity = ENTITY_INDEX.get(email)
        if entity:
            results.append({"email": email, "name": entity["name"], id_field: entity[id_field]})
        else:
            results.append({"email": email, "error": "not found"})
    return json.dumps({"domain": domain, "results": results})


@mcp.tool()
def list_all_entities() -> str:
    """List all known entities and their cross-domain IDs. Returns full index."""
    return json.dumps({"count": len(ENTITY_INDEX), "entities": ENTITY_INDEX})



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
