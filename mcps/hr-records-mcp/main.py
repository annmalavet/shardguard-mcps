from mcp.server import transport_security as _ts
from mcp.server.transport_security import TransportSecuritySettings as _TSS
_ts.TransportSecurityMiddleware.__init__ = lambda self, settings=None: setattr(self, "settings", _TSS(enable_dns_rebinding_protection=False))

from mcp.server.fastmcp import FastMCP
import json
import os

mcp = FastMCP("hr-records-mcp")

EMPLOYEES = {
    "E001": {
        "id": "E001",
        "name": "Sarah Chen",
        "email": "sarah.chen@company.com",
        "ssn": "412-23-8901",
        "salary": 125000,
        "department": "Engineering",
        "role": "Senior Software Engineer",
        "manager_id": "E005",
        "start_date": "2021-03-15",
        "performance_rating": 4.5,
        "address": "123 Oak Street, San Francisco, CA 94102",
        "phone": "415-555-0192",
        "bank_account": "****4521",
    },
    "E002": {
        "id": "E002",
        "name": "Marcus Williams",
        "email": "marcus.williams@company.com",
        "ssn": "530-44-2210",
        "salary": 98000,
        "department": "Marketing",
        "role": "Marketing Manager",
        "manager_id": "E006",
        "start_date": "2019-07-01",
        "performance_rating": 3.8,
        "address": "456 Pine Ave, Austin, TX 78701",
        "phone": "512-555-0384",
        "bank_account": "****9823",
    },
    "E003": {
        "id": "E003",
        "name": "Priya Patel",
        "email": "priya.patel@company.com",
        "ssn": "621-55-3309",
        "salary": 145000,
        "department": "Engineering",
        "role": "Staff Engineer",
        "manager_id": "E005",
        "start_date": "2018-11-12",
        "performance_rating": 4.9,
        "address": "789 Maple Dr, Seattle, WA 98101",
        "phone": "206-555-0571",
        "bank_account": "****3344",
    },
    "E004": {
        "id": "E004",
        "name": "James Okafor",
        "email": "james.okafor@company.com",
        "ssn": "744-66-1198",
        "salary": 78000,
        "department": "HR",
        "role": "HR Coordinator",
        "manager_id": "E007",
        "start_date": "2022-01-10",
        "performance_rating": 4.1,
        "address": "321 Elm Blvd, Chicago, IL 60601",
        "phone": "312-555-0729",
        "bank_account": "****6677",
    },
    "E005": {
        "id": "E005",
        "name": "Linda Reyes",
        "email": "linda.reyes@company.com",
        "ssn": "815-77-4420",
        "salary": 195000,
        "department": "Engineering",
        "role": "VP Engineering",
        "manager_id": None,
        "start_date": "2016-05-20",
        "performance_rating": 4.7,
        "address": "654 Birch Ln, New York, NY 10001",
        "phone": "212-555-0918",
        "bank_account": "****2255",
    },
}


@mcp.tool()
def search_employees(query: str) -> str:
    """Search employees by name or department. Returns basic info only."""
    query = query.lower()
    results = []
    for emp in EMPLOYEES.values():
        if query in emp["name"].lower() or query in emp["department"].lower():
            results.append({
                "id": emp["id"],
                "name": emp["name"],
                "department": emp["department"],
                "role": emp["role"],
                "email": emp["email"],
            })
    if not results:
        return json.dumps({"results": [], "message": "No employees found."})
    return json.dumps({"results": results})


@mcp.tool()
def get_employee_record(employee_id: str) -> str:
    """Get the full employee record including sensitive PII such as SSN, salary, and address."""
    emp = EMPLOYEES.get(employee_id.upper())
    if not emp:
        return json.dumps({"error": f"Employee {employee_id} not found."})
    return json.dumps(emp)


@mcp.tool()
def get_employee_salary(employee_id: str) -> str:
    """Get the salary for a specific employee."""
    emp = EMPLOYEES.get(employee_id.upper())
    if not emp:
        return json.dumps({"error": f"Employee {employee_id} not found."})
    return json.dumps({
        "id": emp["id"],
        "name": emp["name"],
        "salary": emp["salary"],
    })


@mcp.tool()
def update_employee_record(employee_id: str, field: str, value: str) -> str:
    """Update a field on an employee record. Allowed fields: role, department, phone, address."""
    allowed_fields = {"role", "department", "phone", "address"}
    emp = EMPLOYEES.get(employee_id.upper())
    if not emp:
        return json.dumps({"error": f"Employee {employee_id} not found."})
    if field not in allowed_fields:
        return json.dumps({"error": f"Field '{field}' is not updatable. Allowed: {sorted(allowed_fields)}"})
    old_value = emp[field]
    emp[field] = value
    return json.dumps({
        "id": emp["id"],
        "name": emp["name"],
        "field": field,
        "old_value": old_value,
        "new_value": value,
        "status": "updated",
    })


@mcp.tool()
def list_departments() -> str:
    """List all departments and the number of employees in each."""
    counts = {}
    for emp in EMPLOYEES.values():
        dept = emp["department"]
        counts[dept] = counts.get(dept, 0) + 1
    return json.dumps({"departments": counts})


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
