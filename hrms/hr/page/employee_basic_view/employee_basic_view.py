import frappe

@frappe.whitelist()
def get_employee_info():
    user = frappe.session.user

    # Fetching employee details based on the logged-in user
    employee = frappe.get_value("Employee", {"user_id": user}, ["employee_name", "name", "department", "designation"], as_dict=True)

    if not employee:
        return {"employee_name": "N/A", "employee_id": "N/A", "department": "N/A", "designation": "N/A"}

    return {
        "employee_name": employee.employee_name,
        "employee_id": employee.name,
        "department": employee.department,
        "designation": employee.designation
    }
