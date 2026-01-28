import frappe
from frappe.utils import getdate
from collections import defaultdict
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import timedelta

# Logger setup
LOG_FILE = os.path.join(
    frappe.get_site_path(), "logs", "contractual_attendance_migration.log"
)

logger = logging.getLogger("contractual_attendance_migration")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Entry point
def migrate_contractual_attendance(start_date, cutoff_date):
    """
    One-time migration:
    - Attendance date = IN date
    - OUT may be same day or next day
    - Already-linked checkins are ignored
    """
    start_date = getdate(start_date)
    cutoff_date = getdate(cutoff_date)

    logger.info("=" * 80)
    logger.info(f"START migration | window={start_date} → {cutoff_date}")
    logger.info("=" * 80)

    checkins = frappe.get_all(
        "Employee Checkin",
        filters={
            "attendance": ["is", "not set"],
            "shift": "Contractual_Emp",
            "time": [
                "between",
                [
                    f"{start_date} 00:00:00",
                    f"{cutoff_date + timedelta(days=1)} 23:59:59",
                ],
            ],
        },
        fields=["name", "employee", "time", "log_type"],
        order_by="employee, time",
    )

    if not checkins:
        logger.info("No pending checkins")
        return

    emp_logs = defaultdict(list)
    for c in checkins:
        emp_logs[c.employee].append(c)

    emp_master = {
        e.name: e
        for e in frappe.get_all("Employee", fields=["name", "company", "department"])
    }

    total_created = 0

    for employee, logs in emp_logs.items():
        frappe.db.begin()
        try:
            total_created += _process_employee(employee, logs, emp_master, start_date, cutoff_date)
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            logger.exception(f"FAILED employee {employee}")

    logger.info(f"END migration | attendance created={total_created}")
    logger.info("=" * 80)

# Employee-level processing
def _process_employee(employee, logs, emp_master, start_date, cutoff_date):
    logs.sort(key=lambda x: x.time)
    MAX_SHIFT_SECONDS = 16 * 3600

    # Group INs and OUTs by IN-date
    daily_logs = defaultdict(lambda: {"ins": [], "outs": []})
    for log in logs:
        log_date = getdate(log.time)
        if start_date <= log_date <= cutoff_date:
            if log.log_type == "IN":
                daily_logs[log_date]["ins"].append(log)
            else:
                daily_logs[log_date]["outs"].append(log)

    created = 0
    for att_date, day_logs in sorted(daily_logs.items()):
        if frappe.db.exists(
            "Attendance",
            {"employee": employee, "attendance_date": att_date, "docstatus": ["<", 2]},
        ):
            continue

        ins = sorted(day_logs["ins"], key=lambda x: x.time)
        outs = sorted(day_logs["outs"], key=lambda x: x.time)

        if not ins and not outs:
            continue

        # Determine first_in and last_out according to rules
        if ins and outs:
            first_in = ins[0]
            valid_outs = [o for o in outs if getdate(o.time) in (att_date, att_date + timedelta(days=1))]
            if not valid_outs:
                continue
            last_out = valid_outs[-1]

        elif ins and not outs:
            # only IN exists → cannot create attendance
            continue

        elif outs and not ins:
            # only OUT exists → pair with first OUT as IN (use first OUT's date)
            first_in = outs[0]
            last_out = outs[-1]

        # Validate duration
        duration = (last_out.time - first_in.time).total_seconds()
        if duration <= 0 or duration > MAX_SHIFT_SECONDS:
            logger.info(f"Invalid duration | {employee} | {first_in.time} → {last_out.time}")
            continue

        created += _create_attendance(employee, att_date, first_in, last_out, emp_master)

    return created

# Attendance creation
def _create_attendance(employee, att_date, first_in, last_out, emp_master):
    total_seconds = (last_out.time - first_in.time).total_seconds()
    hours = round(total_seconds / 3600, 2)

    status = "Present" if hours >= 8 else "Half Day"
    comment = None if hours >= 8 else "Marked Half Day: working hours less than 8 hours"

    emp = emp_master.get(employee)

    att = frappe.new_doc("Attendance")
    att.update({
        "employee": employee,
        "attendance_date": att_date,
        "status": status,
        "working_hours": hours,
        "in_time": first_in.time,
        "out_time": last_out.time,
        "company": emp.company if emp else None,
        "department": emp.department if emp else None,
        "shift": "Contractual_Emp",
    })

    att.insert(ignore_permissions=True)
    att.submit()

    if comment:
        att.add_comment("Comment", comment)

    frappe.db.set_value(
        "Employee Checkin",
        {"name": ["in", [first_in.name, last_out.name]]},
        "attendance",
        att.name,
    )

    logger.info(f"{employee} | {att_date} | {status} | {hours}h")
    return 1
