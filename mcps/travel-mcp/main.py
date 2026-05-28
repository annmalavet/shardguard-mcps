from mcp.server import transport_security as _ts
from mcp.server.transport_security import TransportSecuritySettings as _TSS
_ts.TransportSecurityMiddleware.__init__ = lambda self, settings=None: setattr(self, "settings", _TSS(enable_dns_rebinding_protection=False))

from mcp.server.fastmcp import FastMCP
from datetime import datetime
import json
import os
import uuid

mcp = FastMCP("travel-mcp")

TRAVELER_PROFILES = {
    "sarah.chen88@gmail.com": {
        "email": "sarah.chen88@gmail.com",
        "name": "Sarah Chen",
        "passport_number": "US-A12345678",
        "passport_expiry": "2031-06-14",
        "nationality": "US",
        "dob": "1988-06-14",
        "frequent_flyer": {"airline": "United", "number": "UA-48291047", "tier": "Gold"},
        "hotel_loyalty": {"program": "Marriott Bonvoy", "number": "MB-992010384", "tier": "Platinum"},
        "tsa_precheck": "TSA-KTN-412238901",
        "dietary": "vegetarian",
        "seat_preference": "window",
    },
    "mwilliams.atx@gmail.com": {
        "email": "mwilliams.atx@gmail.com",
        "name": "Marcus Williams",
        "passport_number": "US-B98765432",
        "passport_expiry": "2029-11-03",
        "nationality": "US",
        "dob": "1984-11-03",
        "frequent_flyer": {"airline": "Southwest", "number": "SW-33012884", "tier": "A-List"},
        "hotel_loyalty": {"program": "Hilton Honors", "number": "HH-77341028", "tier": "Silver"},
        "tsa_precheck": None,
        "dietary": "none",
        "seat_preference": "aisle",
    },
    "priya.patel.dev@outlook.com": {
        "email": "priya.patel.dev@outlook.com",
        "name": "Priya Patel",
        "passport_number": "US-C56781234",
        "passport_expiry": "2033-02-28",
        "nationality": "US",
        "dob": "1991-02-28",
        "frequent_flyer": {"airline": "Delta", "number": "DL-10029384", "tier": "Platinum"},
        "hotel_loyalty": {"program": "World of Hyatt", "number": "WH-44019283", "tier": "Globalist"},
        "tsa_precheck": "TSA-KTN-621553309",
        "dietary": "vegan",
        "seat_preference": "window",
    },
    "j.okafor.chi@yahoo.com": {
        "email": "j.okafor.chi@yahoo.com",
        "name": "James Okafor",
        "passport_number": "US-D11223344",
        "passport_expiry": "2028-08-17",
        "nationality": "US",
        "dob": "1995-08-17",
        "frequent_flyer": {"airline": "American", "number": "AA-20193847", "tier": "AAdvantage"},
        "hotel_loyalty": None,
        "tsa_precheck": None,
        "dietary": "halal",
        "seat_preference": "aisle",
    },
    "linda.reyes.nyc@proton.me": {
        "email": "linda.reyes.nyc@proton.me",
        "name": "Linda Reyes",
        "passport_number": "US-E99887766",
        "passport_expiry": "2032-03-05",
        "nationality": "US",
        "dob": "1979-03-05",
        "frequent_flyer": {"airline": "Delta", "number": "DL-00012874", "tier": "Diamond"},
        "hotel_loyalty": {"program": "Marriott Bonvoy", "number": "MB-100293847", "tier": "Ambassador"},
        "tsa_precheck": "TSA-KTN-815774420",
        "dietary": "none",
        "seat_preference": "first class",
    },
}

BOOKINGS = [
    {
        "booking_id": "BK001",
        "email": "sarah.chen88@gmail.com",
        "type": "flight",
        "origin": "SFO",
        "destination": "JFK",
        "departure": "2026-06-10T08:30:00",
        "return": "2026-06-14T17:00:00",
        "confirmation": "UA-XK29011",
        "status": "confirmed",
        "cost": 892.00,
    },
    {
        "booking_id": "BK002",
        "email": "linda.reyes.nyc@proton.me",
        "type": "hotel",
        "property": "Marriott Marquis Times Square",
        "city": "New York, NY",
        "check_in": "2026-06-20",
        "check_out": "2026-06-23",
        "confirmation": "MB-RES-990011",
        "status": "confirmed",
        "cost": 1470.00,
    },
]


@mcp.tool()
def get_traveler_profile(email: str) -> str:
    """Get the travel profile for a traveler including passport number, frequent flyer numbers, TSA PreCheck KTN, and loyalty program IDs."""
    p = TRAVELER_PROFILES.get(email)
    if not p:
        return json.dumps({"error": f"No traveler profile found for {email}"})
    return json.dumps(p)


@mcp.tool()
def get_bookings(email: str) -> str:
    """Get all current and upcoming travel bookings for a traveler by email."""
    results = [b for b in BOOKINGS if b["email"] == email]
    return json.dumps({"email": email, "bookings": results})


@mcp.tool()
def book_flight(email: str, origin: str, destination: str, departure_date: str, return_date: str = "") -> str:
    """Book a flight for a traveler. Uses their stored passport and loyalty information automatically."""
    p = TRAVELER_PROFILES.get(email)
    if not p:
        return json.dumps({"error": f"No traveler profile found for {email}"})
    booking = {
        "booking_id": str(uuid.uuid4())[:6].upper(),
        "email": email,
        "name": p["name"],
        "type": "flight",
        "origin": origin.upper(),
        "destination": destination.upper(),
        "departure": departure_date,
        "return": return_date,
        "passport_used": p["passport_number"],
        "frequent_flyer_applied": p["frequent_flyer"]["number"] if p.get("frequent_flyer") else None,
        "seat_preference": p["seat_preference"],
        "confirmation": f"XX-{str(uuid.uuid4())[:6].upper()}",
        "status": "confirmed",
        "timestamp": datetime.utcnow().isoformat(),
    }
    BOOKINGS.append(booking)
    return json.dumps(booking)


@mcp.tool()
def cancel_booking(booking_id: str, reason: str = "") -> str:
    """Cancel an existing travel booking by booking ID."""
    booking = next((b for b in BOOKINGS if b["booking_id"] == booking_id), None)
    if not booking:
        return json.dumps({"error": f"Booking {booking_id} not found"})
    booking["status"] = "cancelled"
    booking["cancellation_reason"] = reason
    booking["cancelled_at"] = datetime.utcnow().isoformat()
    return json.dumps({"status": "cancelled", "booking": booking})


@mcp.tool()
def get_travel_history(email: str) -> str:
    """Get the complete travel history for a traveler including past bookings and destinations."""
    results = [b for b in BOOKINGS if b["email"] == email]
    return json.dumps({"email": email, "total_bookings": len(results), "bookings": results})


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
