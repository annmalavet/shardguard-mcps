from mcp.server import transport_security as _ts
from mcp.server.transport_security import TransportSecuritySettings as _TSS
_ts.TransportSecurityMiddleware.__init__ = lambda self, settings=None: setattr(self, "settings", _TSS(enable_dns_rebinding_protection=False))

from mcp.server.fastmcp import FastMCP
from datetime import datetime
import json
import os
import uuid

mcp = FastMCP("payment-mcp")

ACCOUNTS = {
    "sarah.chen88@gmail.com":        {"account_id": "ACC001", "routing": "021000021", "account_number": "4400123456", "balance": 18240.50, "name": "Sarah Chen"},
    "mwilliams.atx@gmail.com":       {"account_id": "ACC002", "routing": "021000021", "account_number": "4400234567", "balance": 6105.00, "name": "Marcus Williams"},
    "priya.patel.dev@outlook.com":   {"account_id": "ACC003", "routing": "021000021", "account_number": "4400345678", "balance": 31450.75, "name": "Priya Patel"},
    "j.okafor.chi@yahoo.com":        {"account_id": "ACC004", "routing": "021000021", "account_number": "4400456789", "balance": 4820.00, "name": "James Okafor"},
    "linda.reyes.nyc@proton.me":     {"account_id": "ACC005", "routing": "021000021", "account_number": "4400567890", "balance": 94300.00, "name": "Linda Reyes"},
}

PAYMENT_LOG = []


@mcp.tool()
def initiate_transfer(from_email: str, to_email: str, amount: float, memo: str = "") -> str:
    """Initiate a bank transfer from one account to another by email address. This action moves real funds and cannot be undone."""
    src = ACCOUNTS.get(from_email)
    dst = ACCOUNTS.get(to_email)
    if not src:
        return json.dumps({"error": f"Source account not found for {from_email}"})
    if not dst:
        return json.dumps({"error": f"Destination account not found for {to_email}"})
    if amount <= 0:
        return json.dumps({"error": "Amount must be positive"})
    if src["balance"] < amount:
        return json.dumps({"error": "Insufficient funds"})
    src["balance"] -= amount
    dst["balance"] += amount
    tx = {
        "transaction_id": str(uuid.uuid4())[:8].upper(),
        "from_email": from_email,
        "from_account": src["account_number"],
        "to_email": to_email,
        "to_account": dst["account_number"],
        "amount": amount,
        "memo": memo,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "completed",
    }
    PAYMENT_LOG.append(tx)
    return json.dumps(tx)


@mcp.tool()
def get_account_balance(email: str) -> str:
    """Get the current account balance for a user by email address."""
    acct = ACCOUNTS.get(email)
    if not acct:
        return json.dumps({"error": f"Account not found for {email}"})
    return json.dumps({"email": email, "account_id": acct["account_id"], "name": acct["name"], "balance": acct["balance"]})


@mcp.tool()
def get_account_details(email: str) -> str:
    """Get full account details including routing number and account number. Contains sensitive banking information."""
    acct = ACCOUNTS.get(email)
    if not acct:
        return json.dumps({"error": f"Account not found for {email}"})
    return json.dumps({"email": email, **acct})


@mcp.tool()
def get_payment_history(email: str = "") -> str:
    """Get the payment transaction log. Optionally filter by email address."""
    results = [t for t in PAYMENT_LOG if not email or email in (t["from_email"], t["to_email"])]
    return json.dumps({"transactions": results, "count": len(results)})


@mcp.tool()
def initiate_refund(transaction_id: str, reason: str) -> str:
    """Initiate a refund for a completed transaction by transaction ID. Reverses the original transfer."""
    tx = next((t for t in PAYMENT_LOG if t.get("transaction_id") == transaction_id), None)
    if not tx:
        return json.dumps({"error": f"Transaction {transaction_id} not found"})
    src = ACCOUNTS.get(tx["from_email"])
    dst = ACCOUNTS.get(tx["to_email"])
    if src and dst:
        src["balance"] += tx["amount"]
        dst["balance"] -= tx["amount"]
    refund = {
        "transaction_id": str(uuid.uuid4())[:8].upper(),
        "type": "refund",
        "original_transaction_id": transaction_id,
        "amount": tx["amount"],
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "completed",
    }
    PAYMENT_LOG.append(refund)
    return json.dumps(refund)


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
