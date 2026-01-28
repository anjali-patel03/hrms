# hrms/api/migrate_data.py
import frappe, uuid, json

@frappe.whitelist(allow_guest=True)
def enqueue_migration_job(data):
    if isinstance(data, str):
        data = frappe.parse_json(data)

    file_marker = str(uuid.uuid4())

    frappe.enqueue(
        method="hrms.api.migrate_data.process_migration",
        queue="default",
        is_async=True,
        data=data.get("data_list"),
        file_marker=file_marker,
	timeout=900
    )

    return {"status": "queued", "file_marker": file_marker}


def process_migration(data, file_marker):
    import csv, io

    if isinstance(data, str):
        data = json.loads(data)

    results = []

    for idx, row in enumerate(data):
        try:
            required_fields = ["first_name", "last_name", "gender", "date_of_birth",
                               "date_of_joining", "status", "company", "ph_no",
                               "user_id", "address", "department", "designation", "abbr", "citizen_id"]

            for field in required_fields:
                if field not in row or not row[field]:
                    raise Exception(f"Record {idx + 1}: Missing required field '{field}'.")

            # Create Company if not exists
            if not frappe.db.exists("Company", row["company"]):
                frappe.get_doc({
                    "doctype": "Company",
                    "company_name": row["company"],
                    "abbr": row["abbr"],
                    "default_currency": "INR",
                    "country": "India"
                }).insert(ignore_permissions=True)

            # Create Department if not exists
            department_name = frappe.db.get_value("Department",
                                                  {"department_name": row["department"], "company": row["company"]},
                                                  "name")
            if not department_name:
                dept_doc = frappe.get_doc({
                    "doctype": "Department",
                    "department_name": row["department"],
                    "company": row["company"]
                }).insert(ignore_permissions=True)
                department_name = dept_doc.name

            # Create Designation if not exists
            if not frappe.db.exists("Designation", {"designation_name": row["designation"]}):
                frappe.get_doc({
                    "doctype": "Designation",
                    "designation_name": row["designation"]
                }).insert(ignore_permissions=True)

            # Create User
            user = frappe.get_doc({
                "doctype": "User",
                "email": row["user_id"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "send_welcome_email": 0,
                "new_password": "Test@123",
                "gender": row["gender"],
                "mobile_no": row["ph_no"],
                "roles": [{"role": "Employee"}],
                "block_modules": [
                    {"module": "Integrations"},
                    {"module": "Core"},
                    {"module": "Website"},
                    {"module": "Automation"}
                ],
                "default_app": "hrms",
            })
            user.insert(ignore_permissions=True)

            # Create Employee
            employee = frappe.get_doc({
                "doctype": "Employee",
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "gender": row["gender"],
                "date_of_birth": row["date_of_birth"],
                "date_of_joining": row["date_of_joining"],
                "status": row["status"],
                "company": row["company"],
                "cell_number": row["ph_no"],
                "current_address": row["address"],
                "user_id": user.name,
                "leave_approver": "hr_admin@bmcinternal.com",
                "department": department_name,
                "designation": row["designation"]
            })
            employee.insert(ignore_permissions=True)
            frappe.db.commit()

            results.append({
                "Record": idx + 1,
                "Citizen ID": row["citizen_id"],
                "Status": "Success",
                "Error": ""
            })

        except Exception as e:
            frappe.db.rollback()
            results.append({
                "Record": idx + 1,
                "Citizen ID": row.get("citizen_id"),
                "Status": "Error",
                "Error": str(e)
            })

    # Create and attach CSV file
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["Record", "Citizen ID", "Status", "Error"])
    writer.writeheader()
    writer.writerows(results)

    frappe.get_doc({
        "doctype": "File",
        "file_name": f"migration_result_{file_marker}.csv",
        "is_private": 0,
        "content": output.getvalue()
    }).insert(ignore_permissions=True)

    frappe.db.commit()

#    frappe.enqueue(
 #       method="hrms.api.migrate_data.delete_file_later",
  #      queue="long",
   #     is_async=True,
   #     file_marker=file_marker,
    #    now=False,
     #   timeout=3600
   # )

def delete_file_later(file_marker):
    file_name = f"migration_result_{file_marker}.csv"
    file_doc = frappe.db.exists("File", {"file_name": file_name})

    if file_doc:
        try:
            frappe.delete_doc("File", file_doc, ignore_permissions=True)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(str(e), "Error deleting migration file")
