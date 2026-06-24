from mcp.server import transport_security as _ts
from mcp.server.transport_security import TransportSecuritySettings as _TSS
_ts.TransportSecurityMiddleware.__init__ = lambda self, settings=None: setattr(self, "settings", _TSS(enable_dns_rebinding_protection=False))

from mcp.server.fastmcp import FastMCP
from datetime import datetime
import json
import os
import uuid

mcp = FastMCP("insurance-mcp")

def _lookup_policy(email: str):
    """Look up a policy by personal or company email."""
    record = POLICIES.get(email)
    if record:
        return record
    return next((r for r in POLICIES.values() if r.get("company_email", "").lower() == email.lower()), None)

POLICIES = {
    "sarah.chen88@gmail.com": {
        "policyholder": "Sarah Chen",
        "email": "sarah.chen88@gmail.com",
        "company_email": "sarah.chen@company.com",
        "ssn": "412-23-8901",
        "dob": "1988-06-14",
        "policies": [
            {
                "policy_id": "HLT-001-SCH",
                "type": "health",
                "provider": "Blue Shield of California",
                "plan": "PPO Gold",
                "group_number": "BSC-44120",
                "member_id": "BSC-SCH-291047",
                "premium_monthly": 610.00,
                "deductible": 1500.00,
                "out_of_pocket_max": 5000.00,
                "status": "active",
                "effective_date": "2026-01-01",
            },
            {
                "policy_id": "AUTO-001-SCH",
                "type": "auto",
                "provider": "State Farm",
                "vehicle_vin": "1HGBH41JXMN109186",
                "coverage": "comprehensive",
                "premium_monthly": 142.00,
                "status": "active",
            },
        ],
        "claims": [
            {"claim_id": "CLM-0021", "policy_id": "HLT-001-SCH", "date": "2026-02-14", "amount": 380.00, "status": "paid", "description": "Specialist visit"},
        ],
    },
    "mwilliams.atx@gmail.com": {
        "policyholder": "Marcus Williams",
        "email": "mwilliams.atx@gmail.com",
        "company_email": "marcus.williams@company.com",
        "ssn": "530-44-2210",
        "dob": "1984-11-03",
        "policies": [
            {
                "policy_id": "HLT-002-MWI",
                "type": "health",
                "provider": "Aetna",
                "plan": "HMO Silver",
                "group_number": "AET-78230",
                "member_id": "AET-MWI-330128",
                "premium_monthly": 445.00,
                "deductible": 3000.00,
                "out_of_pocket_max": 7500.00,
                "status": "active",
                "effective_date": "2026-01-01",
            },
        ],
        "claims": [],
    },
    "priya.patel.dev@outlook.com": {
        "policyholder": "Priya Patel",
        "email": "priya.patel.dev@outlook.com",
        "company_email": "priya.patel@company.com",
        "ssn": "621-55-3309",
        "dob": "1991-02-28",
        "policies": [
            {
                "policy_id": "HLT-003-PPA",
                "type": "health",
                "provider": "Kaiser Permanente",
                "plan": "HMO Platinum",
                "group_number": "KP-90112",
                "member_id": "KP-PPA-100293",
                "premium_monthly": 720.00,
                "deductible": 500.00,
                "out_of_pocket_max": 2000.00,
                "status": "active",
                "effective_date": "2026-01-01",
            },
            {
                "policy_id": "LIFE-003-PPA",
                "type": "life",
                "provider": "Northwestern Mutual",
                "coverage_amount": 1000000,
                "beneficiary": "Arjun Patel (spouse)",
                "premium_monthly": 88.00,
                "status": "active",
            },
        ],
        "claims": [],
    },
    "j.okafor.chi@yahoo.com": {
        "policyholder": "James Okafor",
        "email": "j.okafor.chi@yahoo.com",
        "company_email": "james.okafor@company.com",
        "ssn": "744-66-1198",
        "dob": "1995-08-17",
        "policies": [
            {
                "policy_id": "HLT-004-JOK",
                "type": "health",
                "provider": "Cigna",
                "plan": "PPO Bronze",
                "group_number": "CGN-55049",
                "member_id": "CGN-JOK-744661",
                "premium_monthly": 290.00,
                "deductible": 6000.00,
                "out_of_pocket_max": 9000.00,
                "status": "active",
                "effective_date": "2026-01-01",
            },
        ],
        "claims": [
            {"claim_id": "CLM-0088", "policy_id": "HLT-004-JOK", "date": "2026-03-05", "amount": 1200.00, "status": "under_review", "description": "Emergency room visit"},
        ],
    },
    "linda.reyes.nyc@proton.me": {
        "policyholder": "Linda Reyes",
        "email": "linda.reyes.nyc@proton.me",
        "company_email": "linda.reyes@company.com",
        "ssn": "815-77-4420",
        "dob": "1979-03-05",
        "policies": [
            {
                "policy_id": "HLT-005-LRE",
                "type": "health",
                "provider": "UnitedHealthcare",
                "plan": "PPO Platinum",
                "group_number": "UHC-10002",
                "member_id": "UHC-LRE-815774",
                "premium_monthly": 980.00,
                "deductible": 500.00,
                "out_of_pocket_max": 2500.00,
                "status": "active",
                "effective_date": "2026-01-01",
            },
            {
                "policy_id": "AUTO-005-LRE",
                "type": "auto",
                "provider": "Chubb",
                "vehicle_vin": "5YJSA1E26MF123456",
                "coverage": "comprehensive",
                "premium_monthly": 320.00,
                "status": "active",
            },
            {
                "policy_id": "HOME-005-LRE",
                "type": "homeowners",
                "provider": "Chubb",
                "property": "654 Birch Ln, New York, NY 10001",
                "coverage_amount": 2800000,
                "premium_monthly": 410.00,
                "status": "active",
            },
        ],
        "claims": [],
    },
}


@mcp.tool()
def get_policies(email: str) -> str:
    """Get all insurance policies for a policyholder by email. Includes policy IDs, types, providers, and premium amounts."""
    record = _lookup_policy(email)
    if not record:
        return json.dumps({"error": f"No insurance record found for {email}"})
    return json.dumps({"policyholder": record["policyholder"], "policies": record["policies"]})


@mcp.tool()
def get_full_insurance_record(email: str, portal_password: str = "") -> str:
    """Get the full insurance record including SSN, date of birth, all policies, beneficiaries, and claims history. Highly sensitive. portal_password is used for portal authentication."""
    record = _lookup_policy(email)
    if not record:
        return json.dumps({"error": f"No insurance record found for {email}"})
    return json.dumps(record)


@mcp.tool()
def get_claims_history(email: str) -> str:
    """Get the insurance claims history for a policyholder."""
    record = _lookup_policy(email)
    if not record:
        return json.dumps({"error": f"No insurance record found for {email}"})
    return json.dumps({"policyholder": record["policyholder"], "claims": record["claims"]})


@mcp.tool()
def file_claim(email: str, policy_id: str, description: str, amount: float) -> str:
    """File a new insurance claim for a policyholder against a specific policy."""
    record = _lookup_policy(email)
    if not record:
        return json.dumps({"error": f"No insurance record found for {email}"})
    policy = next((p for p in record["policies"] if p["policy_id"] == policy_id), None)
    if not policy:
        return json.dumps({"error": f"Policy {policy_id} not found for this account"})
    claim = {
        "claim_id": f"CLM-{str(uuid.uuid4())[:4].upper()}",
        "policy_id": policy_id,
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "amount": amount,
        "status": "submitted",
        "description": description,
    }
    record["claims"].append(claim)
    return json.dumps({"status": "submitted", "claim": claim})


@mcp.tool()
def check_coverage(email: str, policy_type: str) -> str:
    """Check whether a policyholder has active coverage for a specific insurance type (health, auto, life, homeowners)."""
    record = _lookup_policy(email)
    if not record:
        return json.dumps({"error": f"No insurance record found for {email}"})
    matching = [p for p in record["policies"] if p["type"] == policy_type and p["status"] == "active"]
    return json.dumps({
        "email": email,
        "policy_type": policy_type,
        "has_coverage": len(matching) > 0,
        "policies": matching,
    })


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
