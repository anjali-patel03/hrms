import frappe
from datetime import datetime

@frappe.whitelist()
def get_current_year_attendance():
    #user = frappe.session.user
    #employee = frappe.db.get_value("Employee", {"user_id": user})

    employee = "HR-EMP-00510"
    if not employee:
        return {}

    year = datetime.today().year
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)

    attendance_records = frappe.get_all(
        'Attendance',
        filters={
            'employee': employee,
            'attendance_date': ['between', (start_date.date(), end_date.date())]
        },
        fields=['attendance_date', 'status']
    )

    # Convert status to heatmap values
    status_map = {
        "Present": 1,
        "Absent": -1,
        # Optional: "Half Day": 0.5, etc.
    }

    attendance_map = {}
    for r in attendance_records:
        status_val = status_map.get(r.status, 0)  # default to 0 for unknown
        attendance_map[str(r.attendance_date)] = status_val

    return attendance_map
