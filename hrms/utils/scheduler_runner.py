import frappe
from hrms.utils.scheduler_job import run_daily_contractual_attendance
from hrms.utils.four_hr_scheduler_job import run_daily_4hr_attendance

def run():
    """
    Safe cron entrypoint.
    Called only via `bench execute`.
    """
    frappe.init(site=frappe.local.site)
    frappe.connect()

    try:
        run_daily_contractual_attendance()
        run_daily_4hr_attendance()
    finally:
        frappe.destroy()
