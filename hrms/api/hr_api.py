# myapp/api/hr_api.py
import requests
import frappe

@frappe.whitelist()
def check_shift(data):
    payload = {
        "employeeId": data["employee_id"],
        "startDate": f"{data['from_date']} 00:00:00",
        "endDate": f"{data['to_date']} 23:59:59",
        "secretKey": "mfhpRkmnpBdLgIqMKPTHfSVW+dLYvoK1Z0ktkqlXAZU="
    }

    response = requests.post("https://dev.bmchealth.in/api/v1/hr-department/hr-migration/check-schedule", json=payload, timeout=5)
    result = response.json()

    if result.get("responseObject") != 0:
        frappe.msgprint("Your duty is scheduled for applied date .")
#    else:
#        frappe.msgprint(msg="Leave approved by HMIS", title="Success", indicator="green")

    return {"status": "ok"}
