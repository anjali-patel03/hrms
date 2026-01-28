import frappe
from frappe.utils import get_datetime

@frappe.whitelist(allow_guest=False)
def checkin_ingest():
    """
    Ingest biometric punches from Machine
    """

    data = frappe.request.get_json()
    if not data:
        frappe.throw("Invalid JSON payload")

    device_id = data.get("device_id")
    punches = data.get("punches")

    if not device_id or not punches:
        frappe.throw("device_id and punches are required")

    inserted = 0
    skipped = 0
    errors = []

    for p in punches:
        try:
            user_id = str(p.get("user_id")).strip()
            timestamp = p.get("timestamp")
            punch_type = p.get("punch_type") or "IN"

            if not user_id or not timestamp:
                skipped += 1
                continue

            punch_time = get_datetime(timestamp)

            employee = frappe.db.get_value(
                "Employee",
                {"attendance_device_id": user_id},
                "name"
            )

            if not employee:
                skipped += 1
                continue

            # Idempotency check
            if frappe.db.exists(
                "Employee Checkin",
                {
                    "employee": employee,
                    "time": punch_time,
                    "device_id": device_id
                }
            ):
                skipped += 1
                continue

            doc = frappe.new_doc("Employee Checkin")
            doc.employee = employee
            doc.time = punch_time
            doc.log_type = punch_type
            doc.device_id = device_id
            doc.checkin_source = "Biometric"
            doc.skip_auto_attendance = 0

            doc.flags.ignore_permissions = True
#            doc.flags.ignore_validate = True
#            doc.flags.ignore_mandatory = True

            doc.insert()

            inserted += 1

        except Exception as e:
            errors.append(str(e))
            skipped += 1

    frappe.db.commit()

    return {
        "status": "ok",
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors
    }
