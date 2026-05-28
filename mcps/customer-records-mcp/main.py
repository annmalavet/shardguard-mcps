from mcp.server import transport_security as _ts
from mcp.server.transport_security import TransportSecuritySettings as _TSS
_ts.TransportSecurityMiddleware.__init__ = lambda self, settings=None: setattr(self, "settings", _TSS(enable_dns_rebinding_protection=False))

from mcp.server.fastmcp import FastMCP
import json
import os

mcp = FastMCP("customer-records-mcp")

CUSTOMERS = {
    "C001": {
        "id": "C001",
        "name": "Sarah Chen",
        "email": "sarah.chen@gmail.com",
        "phone": "415-555-0192",
        "address": "123 Oak Street, San Francisco, CA 94102",
        "loyalty_tier": "gold",
        "loyalty_points": 8420,
        "payment_method": "Visa ****4521",
        "total_spent": 4820.50,
        "purchase_history": [
            {"date": "2025-04-15", "item": "Laptop Stand", "amount": 89.99},
            {"date": "2025-04-28", "item": "Wireless Keyboard", "amount": 149.00},
            {"date": "2025-05-10", "item": "Monitor 27in", "amount": 499.00},
        ],
        "preferences": ["electronics", "productivity tools"],
        "account_created": "2021-02-01",
    },
    "C002": {
        "id": "C002",
        "name": "Marcus Williams",
        "email": "marcus.williams@gmail.com",
        "phone": "512-555-0384",
        "address": "456 Pine Ave, Austin, TX 78701",
        "loyalty_tier": "silver",
        "loyalty_points": 3210,
        "payment_method": "Mastercard ****9823",
        "total_spent": 1940.25,
        "purchase_history": [
            {"date": "2025-03-10", "item": "Desk Lamp", "amount": 45.00},
            {"date": "2025-04-01", "item": "Headphones", "amount": 229.00},
            {"date": "2025-05-05", "item": "USB Hub", "amount": 59.99},
        ],
        "preferences": ["audio", "accessories"],
        "account_created": "2022-08-15",
    },
    "C003": {
        "id": "C003",
        "name": "Priya Patel",
        "email": "priya.patel@gmail.com",
        "phone": "206-555-0571",
        "address": "789 Maple Dr, Seattle, WA 98101",
        "loyalty_tier": "platinum",
        "loyalty_points": 21500,
        "payment_method": "Amex ****3344",
        "total_spent": 12400.00,
        "purchase_history": [
            {"date": "2025-04-20", "item": "Standing Desk", "amount": 899.00},
            {"date": "2025-05-01", "item": "Ergonomic Chair", "amount": 1200.00},
            {"date": "2025-05-18", "item": "4K Monitor", "amount": 799.00},
        ],
        "preferences": ["ergonomics", "home office", "electronics"],
        "account_created": "2019-03-12",
    },
    "C004": {
        "id": "C004",
        "name": "James Okafor",
        "email": "james.okafor@gmail.com",
        "phone": "312-555-0729",
        "address": "321 Elm Blvd, Chicago, IL 60601",
        "loyalty_tier": "bronze",
        "loyalty_points": 980,
        "payment_method": "Visa ****6677",
        "total_spent": 520.75,
        "purchase_history": [
            {"date": "2025-05-02", "item": "Mouse Pad", "amount": 29.99},
            {"date": "2025-05-12", "item": "Webcam", "amount": 119.00},
        ],
        "preferences": ["budget", "accessories"],
        "account_created": "2023-11-01",
    },
    "C005": {
        "id": "C005",
        "name": "Linda Reyes",
        "email": "linda.reyes@gmail.com",
        "phone": "212-555-0918",
        "address": "654 Birch Ln, New York, NY 10001",
        "loyalty_tier": "platinum",
        "loyalty_points": 34800,
        "payment_method": "Amex ****2255",
        "total_spent": 28900.00,
        "purchase_history": [
            {"date": "2025-04-10", "item": "MacBook Pro", "amount": 3499.00},
            {"date": "2025-04-25", "item": "iPad Pro", "amount": 1099.00},
            {"date": "2025-05-20", "item": "AirPods Max", "amount": 549.00},
        ],
        "preferences": ["apple", "premium", "electronics"],
        "account_created": "2017-06-30",
    },
}


@mcp.tool()
def search_customers(query: str) -> str:
    """Search customers by name or email. Returns basic info only, no payment or address details."""
    query = query.lower()
    results = []
    for c in CUSTOMERS.values():
        if query in c["name"].lower() or query in c["email"].lower():
            results.append({
                "id": c["id"],
                "name": c["name"],
                "email": c["email"],
                "loyalty_tier": c["loyalty_tier"],
                "loyalty_points": c["loyalty_points"],
            })
    if not results:
        return json.dumps({"results": [], "message": "No customers found."})
    return json.dumps({"results": results})


@mcp.tool()
def get_customer_record(customer_id: str) -> str:
    """Get the full customer record including address, payment method, and purchase history."""
    c = CUSTOMERS.get(customer_id.upper())
    if not c:
        return json.dumps({"error": f"Customer {customer_id} not found."})
    return json.dumps(c)


@mcp.tool()
def get_purchase_history(customer_id: str) -> str:
    """Get the purchase history for a specific customer."""
    c = CUSTOMERS.get(customer_id.upper())
    if not c:
        return json.dumps({"error": f"Customer {customer_id} not found."})
    return json.dumps({
        "id": c["id"],
        "name": c["name"],
        "total_spent": c["total_spent"],
        "purchase_history": c["purchase_history"],
    })


@mcp.tool()
def get_loyalty_status(customer_id: str) -> str:
    """Get the loyalty tier and points for a specific customer."""
    c = CUSTOMERS.get(customer_id.upper())
    if not c:
        return json.dumps({"error": f"Customer {customer_id} not found."})
    return json.dumps({
        "id": c["id"],
        "name": c["name"],
        "loyalty_tier": c["loyalty_tier"],
        "loyalty_points": c["loyalty_points"],
    })


@mcp.tool()
def update_loyalty_points(customer_id: str, points_delta: int) -> str:
    """Add or subtract loyalty points from a customer account."""
    c = CUSTOMERS.get(customer_id.upper())
    if not c:
        return json.dumps({"error": f"Customer {customer_id} not found."})
    old_points = c["loyalty_points"]
    c["loyalty_points"] = max(0, old_points + points_delta)
    return json.dumps({
        "id": c["id"],
        "name": c["name"],
        "old_points": old_points,
        "new_points": c["loyalty_points"],
        "delta": points_delta,
        "status": "updated",
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
