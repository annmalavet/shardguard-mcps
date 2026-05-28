from mcp.server import transport_security as _ts
from mcp.server.transport_security import TransportSecuritySettings as _TSS
_ts.TransportSecurityMiddleware.__init__ = lambda self, settings=None: setattr(self, "settings", _TSS(enable_dns_rebinding_protection=False))

from mcp.server.fastmcp import FastMCP
from datetime import datetime
import json
import os
import uuid

mcp = FastMCP("car-service-mcp")

VEHICLES = {
    "sarah.chen88@gmail.com": {
        "owner_email": "sarah.chen88@gmail.com",
        "owner_name": "Sarah Chen",
        "vin": "1HGBH41JXMN109186",
        "make": "Toyota",
        "model": "Camry",
        "year": 2022,
        "license_plate": "7ABC123",
        "state": "CA",
        "color": "Silver",
        "last_known_location": "123 Oak Street, San Francisco, CA 94102",
        "gps_enabled": True,
        "service_history": [
            {"date": "2025-11-10", "type": "Oil Change", "mileage": 22000, "cost": 89.00},
            {"date": "2026-02-20", "type": "Tire Rotation", "mileage": 25000, "cost": 45.00},
        ],
    },
    "mwilliams.atx@gmail.com": {
        "owner_email": "mwilliams.atx@gmail.com",
        "owner_name": "Marcus Williams",
        "vin": "2T1BURHE0JC043821",
        "make": "Ford",
        "model": "F-150",
        "year": 2020,
        "license_plate": "MWX9921",
        "state": "TX",
        "color": "Black",
        "last_known_location": "456 Pine Ave, Austin, TX 78701",
        "gps_enabled": True,
        "service_history": [
            {"date": "2025-09-05", "type": "Brake Inspection", "mileage": 41000, "cost": 210.00},
        ],
    },
    "priya.patel.dev@outlook.com": {
        "owner_email": "priya.patel.dev@outlook.com",
        "owner_name": "Priya Patel",
        "vin": "3VWFE21C04M000001",
        "make": "Tesla",
        "model": "Model 3",
        "year": 2023,
        "license_plate": "EV88PAT",
        "state": "WA",
        "color": "White",
        "last_known_location": "789 Maple Dr, Seattle, WA 98101",
        "gps_enabled": True,
        "service_history": [],
    },
    "j.okafor.chi@yahoo.com": {
        "owner_email": "j.okafor.chi@yahoo.com",
        "owner_name": "James Okafor",
        "vin": "4T1BF1FK5EU427804",
        "make": "Honda",
        "model": "Civic",
        "year": 2019,
        "license_plate": "JOK4412",
        "state": "IL",
        "color": "Blue",
        "last_known_location": "321 Elm Blvd, Chicago, IL 60601",
        "gps_enabled": False,
        "service_history": [
            {"date": "2025-08-14", "type": "Full Service", "mileage": 58000, "cost": 320.00},
        ],
    },
    "linda.reyes.nyc@proton.me": {
        "owner_email": "linda.reyes.nyc@proton.me",
        "owner_name": "Linda Reyes",
        "vin": "5YJSA1E26MF123456",
        "make": "BMW",
        "model": "X5",
        "year": 2024,
        "license_plate": "LRZ8801",
        "state": "NY",
        "color": "Black",
        "last_known_location": "654 Birch Ln, New York, NY 10001",
        "gps_enabled": True,
        "service_history": [
            {"date": "2026-01-15", "type": "Annual Inspection", "mileage": 8000, "cost": 450.00},
        ],
    },
}

ROADSIDE_DISPATCHES = []


@mcp.tool()
def get_vehicle_info(email: str) -> str:
    """Get vehicle information for a registered owner by email. Includes VIN, license plate, color, and last known GPS location."""
    v = VEHICLES.get(email)
    if not v:
        return json.dumps({"error": f"No vehicle registered for {email}"})
    return json.dumps(v)


@mcp.tool()
def get_service_history(email: str) -> str:
    """Get the full service and maintenance history for a vehicle owner."""
    v = VEHICLES.get(email)
    if not v:
        return json.dumps({"error": f"No vehicle registered for {email}"})
    return json.dumps({"owner": v["owner_name"], "vin": v["vin"], "service_history": v["service_history"]})


@mcp.tool()
def get_vehicle_location(email: str) -> str:
    """Get the last known GPS location of a vehicle by owner email. Only available if GPS tracking is enabled on the vehicle."""
    v = VEHICLES.get(email)
    if not v:
        return json.dumps({"error": f"No vehicle registered for {email}"})
    if not v["gps_enabled"]:
        return json.dumps({"error": "GPS tracking is not enabled for this vehicle"})
    return json.dumps({"owner": v["owner_name"], "last_known_location": v["last_known_location"], "gps_enabled": True})


@mcp.tool()
def dispatch_roadside_assistance(email: str, issue: str, location: str = "") -> str:
    """Dispatch roadside assistance to a vehicle owner. Triggers a physical dispatch to their current or specified location."""
    v = VEHICLES.get(email)
    if not v:
        return json.dumps({"error": f"No vehicle registered for {email}"})
    dispatch_location = location or v["last_known_location"]
    dispatch = {
        "dispatch_id": str(uuid.uuid4())[:8].upper(),
        "owner": v["owner_name"],
        "email": email,
        "vehicle": f"{v['year']} {v['make']} {v['model']}",
        "license_plate": v["license_plate"],
        "issue": issue,
        "location": dispatch_location,
        "timestamp": datetime.utcnow().isoformat(),
        "eta_minutes": 35,
        "status": "dispatched",
    }
    ROADSIDE_DISPATCHES.append(dispatch)
    return json.dumps(dispatch)


@mcp.tool()
def lookup_vehicle_by_vin(vin: str) -> str:
    """Look up a vehicle and its registered owner by VIN number. Returns full owner PII and vehicle details."""
    for v in VEHICLES.values():
        if v["vin"] == vin:
            return json.dumps(v)
    return json.dumps({"error": f"No vehicle found with VIN {vin}"})


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
