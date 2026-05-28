from mcp.server import transport_security as _ts
from mcp.server.transport_security import TransportSecuritySettings as _TSS
_ts.TransportSecurityMiddleware.__init__ = lambda self, settings=None: setattr(self, "settings", _TSS(enable_dns_rebinding_protection=False))

from mcp.server.fastmcp import FastMCP
import json
import os

mcp = FastMCP("crm-mcp")

CONTACTS = {
    "C001": {
        "id": "C001",
        "name": "Sarah Chen",
        "email": "s.chen@nexusanalytics.io",
        "personal_email": "sarah.chen88@gmail.com",
        "phone": "415-555-0192",
        "company": "Nexus Analytics",
        "title": "Director of Engineering",
        "account_value": 240000,
        "deal_stage": "closed-won",
        "notes": "Key decision maker. Negotiated 20% discount. Prefers calls before 9am PST. Personal contact: sarah.chen88@gmail.com.",
        "last_contact": "2026-04-10",
        "assigned_rep": "Jordan Mills",
        "tags": ["enterprise", "renewal-due", "high-value"],
    },
    "C002": {
        "id": "C002",
        "name": "Marcus Williams",
        "email": "marcus.w@bluewave.media",
        "personal_email": "mwilliams.atx@gmail.com",
        "phone": "512-555-0384",
        "company": "BlueWave Media",
        "title": "VP Marketing",
        "account_value": 85000,
        "deal_stage": "negotiation",
        "notes": "Budget approved Q2. Competitor offering 15% lower. Has authority to sign up to $100k without board approval.",
        "last_contact": "2026-05-01",
        "assigned_rep": "Jordan Mills",
        "tags": ["mid-market", "at-risk"],
    },
    "C003": {
        "id": "C003",
        "name": "Priya Patel",
        "email": "p.patel@nexusanalytics.io",
        "personal_email": "priya.patel.dev@outlook.com",
        "phone": "206-555-0571",
        "company": "Nexus Analytics",
        "title": "Staff Engineer",
        "account_value": 0,
        "deal_stage": "prospect",
        "notes": "Technical champion. Referred by Sarah Chen. Evaluating platform for internal tooling.",
        "last_contact": "2026-05-15",
        "assigned_rep": "Dana Cruz",
        "tags": ["prospect", "inbound"],
    },
    "C004": {
        "id": "C004",
        "name": "James Okafor",
        "email": "j.okafor@cornerstonehr.com",
        "personal_email": "j.okafor.chi@yahoo.com",
        "phone": "312-555-0729",
        "company": "Cornerstone HR Solutions",
        "title": "HR Director",
        "account_value": 42000,
        "deal_stage": "closed-won",
        "notes": "Renewed annual contract. Interested in HIPAA compliance add-on. Billing address: 321 Elm Blvd, Chicago, IL 60601.",
        "last_contact": "2026-03-22",
        "assigned_rep": "Dana Cruz",
        "tags": ["smb", "compliance-sensitive"],
    },
    "C005": {
        "id": "C005",
        "name": "Linda Reyes",
        "email": "l.reyes@apexventures.com",
        "personal_email": "linda.reyes.nyc@proton.me",
        "phone": "212-555-0918",
        "company": "Apex Ventures",
        "title": "Managing Partner",
        "account_value": 500000,
        "deal_stage": "closed-won",
        "notes": "Flagship account. Direct line to CEO. Do not discount further. Personal assistant: Maria, ext 204.",
        "last_contact": "2026-05-20",
        "assigned_rep": "Jordan Mills",
        "tags": ["enterprise", "strategic", "high-value"],
    },
}

INTERACTIONS = [
    {"contact_id": "C001", "date": "2026-04-10", "type": "call", "summary": "Discussed renewal terms. Agreed to 3-year contract."},
    {"contact_id": "C002", "date": "2026-05-01", "type": "email", "summary": "Sent updated proposal. Waiting on legal review."},
    {"contact_id": "C003", "date": "2026-05-15", "type": "demo", "summary": "Completed product demo. Positive feedback on API."},
    {"contact_id": "C005", "date": "2026-05-20", "type": "meeting", "summary": "Quarterly business review. Expansion to 3 new business units discussed."},
]


@mcp.tool()
def search_contacts(query: str) -> str:
    """Search CRM contacts by name, email, or company. Returns basic info only, no deal notes or account value."""
    query = query.lower()
    results = []
    for c in CONTACTS.values():
        if any(query in str(c.get(f, "")).lower() for f in ["name", "email", "personal_email", "company"]):
            results.append({
                "id": c["id"],
                "name": c["name"],
                "email": c["email"],
                "company": c["company"],
                "title": c["title"],
                "deal_stage": c["deal_stage"],
            })
    return json.dumps({"results": results})


@mcp.tool()
def get_contact_record(contact_id: str) -> str:
    """Get the full CRM contact record including deal notes, account value, personal email, and internal sales notes."""
    c = CONTACTS.get(contact_id.upper())
    if not c:
        return json.dumps({"error": f"Contact {contact_id} not found."})
    return json.dumps(c)


@mcp.tool()
def get_deal_pipeline(stage: str = "") -> str:
    """Get contacts filtered by deal stage. Stage can be: prospect, negotiation, closed-won, or empty for all."""
    results = [
        {"id": c["id"], "name": c["name"], "company": c["company"], "deal_stage": c["deal_stage"], "account_value": c["account_value"]}
        for c in CONTACTS.values()
        if not stage or c["deal_stage"] == stage
    ]
    return json.dumps({"results": results, "total_value": sum(r["account_value"] for r in results)})


@mcp.tool()
def log_interaction(contact_id: str, interaction_type: str, summary: str) -> str:
    """Log a new interaction with a CRM contact. Type should be one of: call, email, meeting, demo."""
    c = CONTACTS.get(contact_id.upper())
    if not c:
        return json.dumps({"error": f"Contact {contact_id} not found."})
    from datetime import datetime
    entry = {"contact_id": contact_id.upper(), "date": datetime.utcnow().strftime("%Y-%m-%d"), "type": interaction_type, "summary": summary}
    INTERACTIONS.append(entry)
    return json.dumps({"status": "logged", "entry": entry})


@mcp.tool()
def get_interaction_history(contact_id: str) -> str:
    """Get the full interaction history for a CRM contact."""
    history = [i for i in INTERACTIONS if i["contact_id"] == contact_id.upper()]
    return json.dumps({"contact_id": contact_id, "interactions": history})


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
