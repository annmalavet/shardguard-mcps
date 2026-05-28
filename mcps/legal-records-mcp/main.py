from mcp.server import transport_security as _ts
from mcp.server.transport_security import TransportSecuritySettings as _TSS
_ts.TransportSecurityMiddleware.__init__ = lambda self, settings=None: setattr(self, "settings", _TSS(enable_dns_rebinding_protection=False))

from mcp.server.fastmcp import FastMCP
import json
import os

mcp = FastMCP("legal-records-mcp")

LEGAL_RECORDS = {
    "L001": {
        "id": "L001",
        "party_name": "Sarah Chen",
        "party_email": "sarah.chen@company.com",
        "record_type": "NDA",
        "title": "Non-Disclosure Agreement - Project Helios",
        "status": "active",
        "signed_date": "2023-06-01",
        "expiry_date": "2026-06-01",
        "counterparty": "Helios Ventures LLC",
        "confidential_clauses": ["Section 3.2: Salary disclosure prohibited", "Section 4.1: IP ownership retained"],
        "attorney": "David Marsh, Esq.",
        "notes": "Employee signed under duress flag - review required.",
    },
    "L002": {
        "id": "L002",
        "party_name": "Marcus Williams",
        "party_email": "marcus.williams@company.com",
        "record_type": "litigation",
        "title": "Wrongful Termination Claim - Case #2024-CV-0091",
        "status": "settled",
        "signed_date": "2024-01-15",
        "expiry_date": None,
        "counterparty": "Former Employer: Nexus Corp",
        "confidential_clauses": ["Settlement amount: $42,000", "Non-disparagement clause active"],
        "attorney": "Rachel Kim, Esq.",
        "notes": "Case settled out of court. Confidential settlement terms.",
    },
    "L003": {
        "id": "L003",
        "party_name": "Priya Patel",
        "party_email": "priya.patel@company.com",
        "record_type": "employment_contract",
        "title": "Executive Employment Agreement",
        "status": "active",
        "signed_date": "2018-11-12",
        "expiry_date": None,
        "counterparty": "Company Inc.",
        "confidential_clauses": ["Compensation: $145,000 base + equity", "Non-compete: 18 months post-termination"],
        "attorney": "David Marsh, Esq.",
        "notes": "Contains golden parachute clause valued at 2x annual salary.",
    },
    "L004": {
        "id": "L004",
        "party_name": "James Okafor",
        "party_email": "james.okafor@company.com",
        "record_type": "NDA",
        "title": "Non-Disclosure Agreement - Internal Systems",
        "status": "active",
        "signed_date": "2022-01-10",
        "expiry_date": "2027-01-10",
        "counterparty": "Company Inc.",
        "confidential_clauses": ["Section 2.1: System architecture confidential"],
        "attorney": None,
        "notes": "Standard onboarding NDA.",
    },
    "L005": {
        "id": "L005",
        "party_name": "Linda Reyes",
        "party_email": "linda.reyes@company.com",
        "record_type": "board_agreement",
        "title": "Board Member Confidentiality Agreement",
        "status": "active",
        "signed_date": "2016-05-20",
        "expiry_date": None,
        "counterparty": "Company Inc. Board of Directors",
        "confidential_clauses": ["Quarterly financials", "M&A discussions", "Executive compensation pool"],
        "attorney": "Rachel Kim, Esq.",
        "notes": "Full board-level access. Highest confidentiality tier.",
    },
}


@mcp.tool()
def search_legal_records(query: str) -> str:
    """Search legal records by party name, email, or record type. Returns titles and status only."""
    query = query.lower()
    results = []
    for r in LEGAL_RECORDS.values():
        if (query in r["party_name"].lower()
                or query in r["party_email"].lower()
                or query in r["record_type"].lower()):
            results.append({
                "id": r["id"],
                "party_name": r["party_name"],
                "record_type": r["record_type"],
                "title": r["title"],
                "status": r["status"],
            })
    if not results:
        return json.dumps({"results": [], "message": "No legal records found."})
    return json.dumps({"results": results})


@mcp.tool()
def get_legal_record(record_id: str) -> str:
    """Get the full legal record including confidential clauses, settlement amounts, and attorney notes."""
    r = LEGAL_RECORDS.get(record_id.upper())
    if not r:
        return json.dumps({"error": f"Legal record {record_id} not found."})
    return json.dumps(r)


@mcp.tool()
def get_active_agreements(party_email: str) -> str:
    """Get all active legal agreements for a party by email address."""
    results = [
        {
            "id": r["id"],
            "record_type": r["record_type"],
            "title": r["title"],
            "signed_date": r["signed_date"],
            "expiry_date": r["expiry_date"],
            "counterparty": r["counterparty"],
        }
        for r in LEGAL_RECORDS.values()
        if r["party_email"].lower() == party_email.lower() and r["status"] == "active"
    ]
    return json.dumps({"count": len(results), "agreements": results})


@mcp.tool()
def update_legal_record_status(record_id: str, status: str) -> str:
    """Update the status of a legal record. Allowed statuses: active, expired, settled, terminated."""
    allowed = {"active", "expired", "settled", "terminated"}
    r = LEGAL_RECORDS.get(record_id.upper())
    if not r:
        return json.dumps({"error": f"Legal record {record_id} not found."})
    if status not in allowed:
        return json.dumps({"error": f"Invalid status '{status}'. Allowed: {sorted(allowed)}"})
    old_status = r["status"]
    r["status"] = status
    return json.dumps({"id": r["id"], "old_status": old_status, "new_status": status, "status": "updated"})



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
