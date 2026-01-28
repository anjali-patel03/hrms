import frappe
from rq import Queue
import redis

@frappe.whitelist(allow_guest=True)
def check_status(data):
    job_id = data.get("job_id")

    if not job_id:
        frappe.throw("Please provide 'job_id'.")

    # Return multiple fields
    fields = ["job_id", "status", "job_name", "queue", "started_at", "ended_at"]
    result = frappe.db.get_all(
        "RQ Job",
        filters={
	    "name": ["like", f"%{job_id}"]
#	    "job_name": ["like", "%hrms.api.create_company.company_creation_worker%"],
        }
    )

    if not result:
        return {
            "http_status_code": 404,
            "status": "no job found",
            "job_id": result
        }

    return {
        "http_status_code": 200,
        "status": "found",
	"len": len(result),
        "data": result
    }
