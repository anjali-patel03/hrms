import frappe
from hrms.utils.scheduler_job import run_daily_contractual_attendance
from hrms.utils.four_hr_scheduler_job import run_daily_4hr_attendance
from hrms.utils.seven_eight_hour_scheduler_job import run_daily_7_8hr_attendance
from hrms.utils.nursing_nsg_scheduler_job import run_daily_nursing_attendance
from hrms.utils.pharma_micro_scheduler_job import run_daily_pharma_attendance
from hrms.utils.lab_elab_scheduler_job import run_daily_lab_elab_attendance

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
        run_daily_7_8hr_attendance()
        run_daily_nursing_attendance()
        run_daily_pharma_attendance()
        run_daily_lab_elab_attendance()
    finally:
        frappe.destroy()
