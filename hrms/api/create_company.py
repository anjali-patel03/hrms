# app/hrms/hrms/api/create_company.py
import frappe
import uuid
import re

@frappe.whitelist(allow_guest=True)
def company_creation_api(data):
    if isinstance(data, str):
        data = frappe.parse_json(data)

    job = frappe.enqueue(
        "hrms.api.create_company.company_creation_worker",
        queue="default",
        is_async=True,
        data=data
    )

    return {
        "status": "queued",
        "job_id": job.id,
        "abbr": data.get("abbr"),
        "company_name": data.get("company_name")
    }


def company_creation_worker(data):
    """This is the actual background-safe job handler."""
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            frappe.logger().info(f"[Attempt {attempt}] Creating company: {data['company_name']}")

            abbr = make_unique_abbr(data["abbr"])

            company = frappe.get_doc({
                "doctype": "Company",
                "company_name": data["company_name"],
                "abbr": abbr,
                "default_currency": data["default_currency"],
                "country": data["country"]
            })
            company.insert(ignore_permissions=True)
            frappe.db.commit()
            frappe.logger().info(f"Company Created Successfully with abbr={abbr}")
            return
        except Exception as e:
            frappe.logger().error(f"Attempt {attempt} failed: {str(e)}")
            if attempt == max_retries:
                raise


def make_unique_abbr(base_abbr: str) -> str:
    base_abbr = re.sub(r"\s+", "", base_abbr.strip().upper())  # sanitize
    abbr = base_abbr

    if not frappe.db.exists("Company", {"abbr": abbr}):
        return abbr

    # If it exists, append numbers until unique
    i = 1
    while frappe.db.exists("Company", {"abbr": abbr}):
        abbr = f"{base_abbr}{i}"
        i += 1

    return abbr
