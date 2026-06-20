from mcp.server import transport_security as _ts
from mcp.server.transport_security import TransportSecuritySettings as _TSS
_ts.TransportSecurityMiddleware.__init__ = lambda self, settings=None: setattr(self, "settings", _TSS(enable_dns_rebinding_protection=False))

from mcp.server.fastmcp import FastMCP
import json
import os

mcp = FastMCP("financial-records-mcp")

ACCOUNTS = {
    "ACC001": {
        "id": "ACC001",
        "owner_name": "Sarah Chen",
        "owner_email": "sarah.chen@company.com",
        "account_number": "4021-8833-5521-4401",
        "routing_number": "021000021",
        "account_type": "checking",
        "balance": 24350.87,
        "credit_score": 782,
        "ssn": "412-23-8901",
        "transactions": [
            {"date": "2025-05-01", "amount": -1200.00, "description": "Rent Payment"},
            {"date": "2025-05-03", "amount": -84.50, "description": "Grocery Store"},
            {"date": "2025-05-10", "amount": 5208.33, "description": "Payroll Deposit"},
            {"date": "2025-05-15", "amount": -320.00, "description": "Utility Bill"},
            {"date": "2025-05-20", "amount": -45.99, "description": "Streaming Services"},
        ],
    },
    "ACC002": {
        "id": "ACC002",
        "owner_name": "Marcus Williams",
        "owner_email": "marcus.williams@company.com",
        "account_number": "4021-9912-3344-7723",
        "routing_number": "021000021",
        "account_type": "checking",
        "balance": 8120.44,
        "credit_score": 641,
        "ssn": "530-44-2210",
        "transactions": [
            {"date": "2025-05-01", "amount": -950.00, "description": "Rent Payment"},
            {"date": "2025-05-05", "amount": -210.33, "description": "Car Insurance"},
            {"date": "2025-05-10", "amount": 4083.33, "description": "Payroll Deposit"},
            {"date": "2025-05-18", "amount": -500.00, "description": "Credit Card Payment"},
            {"date": "2025-05-22", "amount": -88.00, "description": "Phone Bill"},
        ],
    },
    "ACC003": {
        "id": "ACC003",
        "owner_name": "Priya Patel",
        "owner_email": "priya.patel@company.com",
        "account_number": "4021-7745-6612-3309",
        "routing_number": "021000021",
        "account_type": "savings",
        "balance": 87450.00,
        "credit_score": 819,
        "ssn": "621-55-3309",
        "transactions": [
            {"date": "2025-05-01", "amount": -2200.00, "description": "Mortgage Payment"},
            {"date": "2025-05-10", "amount": 6041.67, "description": "Payroll Deposit"},
            {"date": "2025-05-10", "amount": 2000.00, "description": "Transfer to Savings"},
            {"date": "2025-05-14", "amount": -150.00, "description": "Gym Membership"},
            {"date": "2025-05-21", "amount": -980.00, "description": "Travel Booking"},
        ],
    },
    "ACC004": {
        "id": "ACC004",
        "owner_name": "James Okafor",
        "owner_email": "james.okafor@company.com",
        "account_number": "4021-6634-9988-1122",
        "routing_number": "021000021",
        "account_type": "checking",
        "balance": 3240.19,
        "credit_score": 598,
        "ssn": "744-66-1198",
        "transactions": [
            {"date": "2025-05-01", "amount": -800.00, "description": "Rent Payment"},
            {"date": "2025-05-10", "amount": 3250.00, "description": "Payroll Deposit"},
            {"date": "2025-05-12", "amount": -200.00, "description": "Student Loan Payment"},
            {"date": "2025-05-16", "amount": -112.45, "description": "Grocery Store"},
            {"date": "2025-05-23", "amount": -60.00, "description": "Electric Bill"},
        ],
    },
    "ACC005": {
        "id": "ACC005",
        "owner_name": "Linda Reyes",
        "owner_email": "linda.reyes@company.com",
        "account_number": "4021-5523-8871-9900",
        "routing_number": "021000021",
        "account_type": "checking",
        "balance": 142800.00,
        "credit_score": 841,
        "ssn": "815-77-4420",
        "transactions": [
            {"date": "2025-05-01", "amount": -4500.00, "description": "Mortgage Payment"},
            {"date": "2025-05-10", "amount": 16250.00, "description": "Payroll Deposit"},
            {"date": "2025-05-11", "amount": 5000.00, "description": "Investment Transfer"},
            {"date": "2025-05-15", "amount": -1200.00, "description": "Property Tax"},
            {"date": "2025-05-20", "amount": -350.00, "description": "Insurance Premium"},
        ],
    },
}


@mcp.tool()
def search_accounts(query: str) -> str:
    """Search accounts by owner name or email. Returns basic info only, no account numbers or SSN."""
    query = query.lower()
    results = []
    for acc in ACCOUNTS.values():
        if query in acc["owner_name"].lower() or query in acc["owner_email"].lower():
            results.append({
                "id": acc["id"],
                "owner_name": acc["owner_name"],
                "owner_email": acc["owner_email"],
                "account_type": acc["account_type"],
            })
    if not results:
        return json.dumps({"results": [], "message": "No accounts found."})
    return json.dumps({"results": results})


@mcp.tool()
def get_account_record(account_id: str) -> str:
    """Get the full account record including account number, routing number, balance, credit score, and SSN."""
    acc = ACCOUNTS.get(account_id.upper())
    if not acc:
        return json.dumps({"error": f"Account {account_id} not found."})
    return json.dumps(acc)


@mcp.tool()
def get_transaction_history(account_id: str) -> str:
    """Get the transaction history for a specific account."""
    acc = ACCOUNTS.get(account_id.upper())
    if not acc:
        return json.dumps({"error": f"Account {account_id} not found."})
    return json.dumps({
        "id": acc["id"],
        "owner_name": acc["owner_name"],
        "transactions": acc["transactions"],
    })


@mcp.tool()
def get_credit_score(account_id: str) -> str:
    """Get the credit score for a specific account holder."""
    acc = ACCOUNTS.get(account_id.upper())
    if not acc:
        return json.dumps({"error": f"Account {account_id} not found."})
    return json.dumps({
        "id": acc["id"],
        "owner_name": acc["owner_name"],
        "credit_score": acc["credit_score"],
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
