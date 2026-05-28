from mcp.server import transport_security as _ts
from mcp.server.transport_security import TransportSecuritySettings as _TSS
_ts.TransportSecurityMiddleware.__init__ = lambda self, settings=None: setattr(self, "settings", _TSS(enable_dns_rebinding_protection=False))

from mcp.server.fastmcp import FastMCP
import json
import os

mcp = FastMCP("medical-records-mcp")

PATIENTS = {
    "P001": {
        "id": "P001",
        "name": "Sarah Chen",
        "email": "sarah.chen@company.com",
        "dob": "1988-04-12",
        "ssn": "412-23-8901",
        "insurance_id": "BCBS-44821-A",
        "blood_type": "A+",
        "diagnoses": ["Type 2 Diabetes", "Hypertension"],
        "medications": ["Metformin 500mg", "Lisinopril 10mg"],
        "allergies": ["Penicillin"],
        "last_visit": "2025-04-10",
        "physician": "Dr. Karen Liu",
        "notes": "Patient managing glucose levels well. Blood pressure stable.",
    },
    "P002": {
        "id": "P002",
        "name": "Marcus Williams",
        "email": "marcus.williams@company.com",
        "dob": "1985-09-23",
        "ssn": "530-44-2210",
        "insurance_id": "AETNA-77312-B",
        "blood_type": "O-",
        "diagnoses": ["Anxiety Disorder", "Seasonal Allergies"],
        "medications": ["Sertraline 50mg", "Loratadine 10mg"],
        "allergies": ["Sulfa drugs"],
        "last_visit": "2025-03-22",
        "physician": "Dr. James Park",
        "notes": "Patient reports improved mood. Continuing current medication regimen.",
    },
    "P003": {
        "id": "P003",
        "name": "Priya Patel",
        "email": "priya.patel@company.com",
        "dob": "1982-01-30",
        "ssn": "621-55-3309",
        "insurance_id": "UHC-99014-C",
        "blood_type": "B+",
        "diagnoses": ["Hypothyroidism"],
        "medications": ["Levothyroxine 75mcg"],
        "allergies": [],
        "last_visit": "2025-05-01",
        "physician": "Dr. Karen Liu",
        "notes": "TSH levels within normal range. Annual checkup scheduled.",
    },
    "P004": {
        "id": "P004",
        "name": "James Okafor",
        "email": "james.okafor@company.com",
        "dob": "1993-06-15",
        "ssn": "744-66-1198",
        "insurance_id": "CIGNA-55209-D",
        "blood_type": "AB+",
        "diagnoses": ["Asthma"],
        "medications": ["Albuterol inhaler"],
        "allergies": ["Aspirin", "Latex"],
        "last_visit": "2025-02-14",
        "physician": "Dr. James Park",
        "notes": "Mild asthma well controlled. Advised to avoid known triggers.",
    },
    "P005": {
        "id": "P005",
        "name": "Linda Reyes",
        "email": "linda.reyes@company.com",
        "dob": "1975-11-08",
        "ssn": "815-77-4420",
        "insurance_id": "BCBS-11038-E",
        "blood_type": "O+",
        "diagnoses": ["Migraine", "High Cholesterol"],
        "medications": ["Sumatriptan 50mg", "Atorvastatin 20mg"],
        "allergies": ["Codeine"],
        "last_visit": "2025-05-15",
        "physician": "Dr. Karen Liu",
        "notes": "Cholesterol improving with medication. Migraine frequency reduced.",
    },
}


@mcp.tool()
def search_patients(query: str) -> str:
    """Search patients by name or email. Returns basic info only, no diagnoses or medications."""
    query = query.lower()
    results = []
    for p in PATIENTS.values():
        if query in p["name"].lower() or query in p["email"].lower():
            results.append({
                "id": p["id"],
                "name": p["name"],
                "email": p["email"],
                "last_visit": p["last_visit"],
                "physician": p["physician"],
            })
    if not results:
        return json.dumps({"results": [], "message": "No patients found."})
    return json.dumps({"results": results})


@mcp.tool()
def get_patient_record(patient_id: str) -> str:
    """Get the full patient record including diagnoses, medications, SSN, and insurance ID."""
    p = PATIENTS.get(patient_id.upper())
    if not p:
        return json.dumps({"error": f"Patient {patient_id} not found."})
    return json.dumps(p)


@mcp.tool()
def get_patient_diagnoses(patient_id: str) -> str:
    """Get the diagnoses and medications for a specific patient."""
    p = PATIENTS.get(patient_id.upper())
    if not p:
        return json.dumps({"error": f"Patient {patient_id} not found."})
    return json.dumps({
        "id": p["id"],
        "name": p["name"],
        "diagnoses": p["diagnoses"],
        "medications": p["medications"],
        "allergies": p["allergies"],
    })


@mcp.tool()
def get_patient_insurance(patient_id: str) -> str:
    """Get the insurance information for a specific patient."""
    p = PATIENTS.get(patient_id.upper())
    if not p:
        return json.dumps({"error": f"Patient {patient_id} not found."})
    return json.dumps({
        "id": p["id"],
        "name": p["name"],
        "insurance_id": p["insurance_id"],
        "blood_type": p["blood_type"],
    })


@mcp.tool()
def update_patient_notes(patient_id: str, notes: str) -> str:
    """Update the physician notes for a patient record."""
    p = PATIENTS.get(patient_id.upper())
    if not p:
        return json.dumps({"error": f"Patient {patient_id} not found."})
    old_notes = p["notes"]
    p["notes"] = notes
    return json.dumps({
        "id": p["id"],
        "name": p["name"],
        "old_notes": old_notes,
        "new_notes": notes,
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
