# hrms/utils/nursing_nsg_scheduler_job.py
import frappe
from frappe.utils import getdate
from datetime import datetime, time, timedelta
from collections import defaultdict
import logging
from logging.handlers import RotatingFileHandler
import os

GRACE_MINUTES = 15
MIN_HALF_DAY_HOURS = 3.5
SHIFT_NAME = "NSG_Paramedics"
REGULAR_HOURS_CAP = 7.5

# Logger setup
LOG_FILE = os.path.join(
    frappe.get_site_path(), "logs", "NSG_Paramedics_scheduler.log"
)

logger = logging.getLogger("NSG_Paramedics_scheduler")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=7
    )
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def run_daily_nursing_attendance():
    today = getdate()
    start_date = today - timedelta(days=6)
    end_date = today

    logger.info("=" * 80)
    logger.info(f"START scheduler | window={start_date} → {end_date}")
    logger.info("=" * 80)

    checkins = frappe.get_all(
        "Employee Checkin",
        filters={
            "attendance": ["is", "not set"],
            "shift": SHIFT_NAME,
            "time": [
                     "between",
                      [
                          f"{start_date} 00:00:00",
                          f"{end_date + timedelta(days=1)} 23:59:59",
                      ],
             ],
           # "time": ["between", [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]],
        },
        fields=["name", "employee", "time", "log_type"],
        order_by="employee, time",
    )

    if not checkins:
        return

    emp_logs = defaultdict(list)

    for c in checkins:
        emp_logs[c.employee].append(c)

    emp_master = {
        e.name: e
        for e in frappe.get_all(
            "Employee", fields=["name", "company", "department"]
        )
    }

    for employee, logs in emp_logs.items():
        try:
            _process_employee_nursing(employee, logs, emp_master)
            frappe.db.commit()

        except Exception:
            frappe.db.rollback()
            frappe.log_error(frappe.get_traceback(), f"Nursing Scheduler Failed: {employee}")
    logger.info("END scheduler")
    logger.info("=" * 80)


def _process_employee_nursing(employee, logs, emp_master):
    logs.sort(key=lambda x: x.time)

    MAX_SHIFT_SECONDS = 16 * 3600  # safety cap

    # Group logs by IN-date
    daily_logs = defaultdict(lambda: {"ins": [], "outs": []})

    for log in logs:
        log_date = getdate(log.time)

        if log.log_type == "IN":
            daily_logs[log_date]["ins"].append(log)

        else:
            # Night shift OUT belongs to previous day
            if log.time.time() <= time(9, 30):
                daily_logs[log_date - timedelta(days=1)]["outs"].append(log)
            else:
                daily_logs[log_date]["outs"].append(log)

    for att_date, day_logs in sorted(daily_logs.items()):
        if frappe.db.exists(
            "Attendance",
            {
                "employee": employee,
                "attendance_date": att_date,
                "docstatus": ["<", 2],
            },
        ):
            continue

        ins = sorted(day_logs["ins"], key=lambda x: x.time)
        outs = sorted(day_logs["outs"], key=lambda x: x.time)

        if not ins:
            continue

        first_in = ins[0]

        # OUT allowed on same day or next day
        valid_outs = [
            o for o in outs
            if getdate(o.time) in (att_date, att_date + timedelta(days=1))
            and o.time > first_in.time
        ]

        if not valid_outs:
            continue

        last_out = valid_outs[-1]

        duration_seconds = (last_out.time - first_in.time).total_seconds()
        if duration_seconds <= 0 or duration_seconds > MAX_SHIFT_SECONDS:
            logger.info(
                f"Invalid duration | {employee} | {first_in.time} → {last_out.time}"
            )
            continue

        _create_nursing_attendance(
            employee,
            att_date,
            first_in,
            last_out,
            emp_master,
        )

# helpers
def _get_applicable_window(att_date, in_dt):
    windows = [
        _window("Morning", time(7, 0), time(14, 30)),
        _window("Noon", time(14, 0), time(21, 30)),
        _window("Night", time(21, 0), time(7, 30)),
    ]

    for w in windows:
        start_dt = datetime.combine(att_date, w["start"])
        end_dt = datetime.combine(att_date, w["end"])

        # Night rollover
        if w["end"] <= w["start"]:
            end_dt += timedelta(days=1)

        eligibility_start = start_dt - timedelta(minutes=30)
        eligibility_end = start_dt + timedelta(hours=1)

        if eligibility_start <= in_dt <= eligibility_end:
            return w

    return None

def _create_nursing_attendance(employee, att_date, first_in, last_out, emp_master):
    working_hours = (last_out.time - first_in.time).total_seconds() / 3600

    # Detect window FIRST (with eligibility rule)
    window = _get_applicable_window(att_date, first_in.time)
    if not window:
        frappe.db.set_value(
            "Employee Checkin",
            {"name": ["in", [first_in.name, last_out.name]]},
            "offshift",
            1,
        )
        return

    overtime_hours = 0

    if working_hours > REGULAR_HOURS_CAP:
        overtime_hours = round(working_hours - REGULAR_HOURS_CAP, 2)

    # Build correct window datetimes (night-safe)
    start_dt = datetime.combine(att_date, window["start"])
    end_dt = datetime.combine(att_date, window["end"])
    if window["end"] <= window["start"]:
        end_dt += timedelta(days=1)

    start_with_grace = start_dt + timedelta(minutes=GRACE_MINUTES)
    end_with_grace = end_dt - timedelta(minutes=GRACE_MINUTES)

    first_in_dt = first_in.time
    last_out_dt = last_out.time

    late_entry = first_in_dt > start_with_grace
    early_exit = last_out_dt < end_with_grace

    # Monthly grace logic
    monthly_count = frappe.db.get_value(
        "Employee", employee, "monthly_grace_count"
    ) or 0

    status = "Present"
    comment = None

    # 1. Hard failure
    if working_hours < MIN_HALF_DAY_HOURS:
        status = "Half Day"
        comment = "Marked Half Day: insufficient working hours"

    # 2. Grace logic ONLY if late/early exists
    elif late_entry or early_exit:
        if monthly_count < 3:
            monthly_count += 1
            frappe.db.set_value(
                "Employee", employee, "monthly_grace_count", monthly_count
            )
        else:
            status = "Half Day"
            comment = "Marked Half Day: grace limit exceeded"

    emp = emp_master.get(employee)

    att = frappe.new_doc("Attendance")
    att.update({
        "employee": employee,
        "attendance_date": att_date,  # IN date
        "status": status,
        "working_hours": round(working_hours, 2),
        "in_time": first_in.time,
        "out_time": last_out.time,
        "company": emp.company if emp else None,
        "department": emp.department if emp else None,
        "shift": SHIFT_NAME,
        "shift_window": window["label"],
        "late_entry": late_entry,
        "early_exit": early_exit,
        "overtime_hours": overtime_hours,
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

    logger.info(
        f"{employee} | {att_date} | {status} | {working_hours:.2f}h | {window['label']}"
    )

def _window(label, start, end):
    start_dt = datetime.combine(datetime.today(), start)
    end_dt = datetime.combine(datetime.today(), end)
    if end <= start:
        end_dt += timedelta(days=1)

    duration_hours = (end_dt - start_dt).total_seconds() / 3600

    return {
        "label": label,
        "start": start,
        "end": end,
        "duration_hours": duration_hours,
    }
