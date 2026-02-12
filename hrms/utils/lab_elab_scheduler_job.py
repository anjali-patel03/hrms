import frappe
from frappe.utils import getdate
from datetime import datetime, time, timedelta
from collections import defaultdict
import logging
from logging.handlers import RotatingFileHandler
import os

# CONSTANTS
SHIFT_NAME = "Lab_and_Elab"
GRACE_MINUTES = 15
MAX_SHIFT_HOURS = 18

# LOGGING SETUP
LOG_FILE = os.path.join(
    frappe.get_site_path(), "logs", "lab_elab_attendance.log"
)

logger = logging.getLogger("LAB_ELAB_attendance")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = RotatingFileHandler(LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=7)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# EMPLOYEE SHIFT WINDOWS
EMPLOYEE_WINDOWS = {}

# BLOOD BANK
BLOOD_BANK_GROUP = [
    "HR-EMP-08192",  # ANIKET ANANT KHEDEKAR
    "HR-EMP-08191",  # AHILYA BIPIN KEDARI
    "HR-EMP-08193",  # SIMRAN SUNIL JADHAV
    "HR-EMP-12516",  # VINAYA VILAS NEVGI
    "HR-EMP-12517",  # SNEHA VIJAY DHADVE
    "HR-EMP-12518",  # VAISHNAVI VIJAY KATKAR
    # "",  # SAVITA SONSURKAR
]

for emp in BLOOD_BANK_GROUP:
    EMPLOYEE_WINDOWS[emp] = {
        "all": [
            ("7AM-2PM", time(7, 0), time(14, 0), 7),
            ("2PM-10PM", time(14, 0), time(22, 0), 8),
            ("10PM-7AM", time(22, 0), time(7, 0), 9),
        ]
    }

# ENDOCRINOLOGY
ENDO_GROUP = ["HR-EMP-10568", "HR-EMP-10566"]  # POOJA SAHADEV DABHOLKAR, SONALI MADHUKAR KADAM
for emp in ENDO_GROUP:
    EMPLOYEE_WINDOWS[emp] = {
        "all": [
            ("8:30AM-3:30PM", time(8, 30), time(15, 30), 7),
            ("8:30AM-12:30PM", time(8, 30), time(12, 30), 4),
        ]
    }

# BIOCHEMISTRY – E-LAB
BIO_ELAB_GROUP = [
    # Add employee IDs here
]

for emp in BIO_ELAB_GROUP:
    EMPLOYEE_WINDOWS[emp] = {
        "all": [
            ("7AM-2PM", time(7, 0), time(14, 0), 7),
            ("9AM-4PM", time(9, 0), time(16, 0), 7),
            ("11AM-6PM", time(11, 0), time(18, 0), 7),
            ("1PM-8PM", time(13, 0), time(20, 0), 7),
            ("3PM-10PM", time(15, 0), time(22, 0), 7),
            ("11PM-6AM", time(23, 0), time(6, 0), 7),
        ]
    }

# SCHEDULER ENTRY
def run_daily_lab_elab_attendance():
    today = getdate()
    start_date = today - timedelta(days=3)

    logger.info("=" * 80)
    logger.info(f"START LAB | window={start_date} → {today}")
    logger.info("=" * 80)

    checkins = frappe.get_all(
        "Employee Checkin",
        filters={
            "attendance": ["is", "not set"],
            "shift": SHIFT_NAME,
            "time": ["between", [f"{start_date} 00:00:00", f"{today} 23:59:59"]],
        },
        fields=["name", "employee", "time", "log_type"],
        order_by="employee, time",
    )

    logger.info(f"TOTAL CHECKINS FOUND: {len(checkins)}")

    emp_logs = defaultdict(list)
    for c in checkins:
        emp_logs[c.employee].append(c)

    for employee, logs in emp_logs.items():
        try:
            logger.info(f"PROCESSING EMPLOYEE {employee} | logs={len(logs)}")
            _process_lab_elab_employee(employee, logs)
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            logger.exception(f"FAILED employee {employee}")

    logger.info("END scheduler")
    logger.info("=" * 80)

# CORE LOGIC
def _process_lab_elab_employee(employee, logs):
    logs.sort(key=lambda x: x.time)
    daily_logs = defaultdict(list)
    for log in logs:
        daily_logs[getdate(log.time)].append(log)

    windows_cfg = EMPLOYEE_WINDOWS.get(employee)
    if not windows_cfg:
        logger.warning(f"{employee} | No shift windows configured.")
        return

    for att_date, day_logs in sorted(daily_logs.items()):
        if frappe.db.exists("Attendance", {"employee": employee, "attendance_date": att_date, "docstatus": ["<", 2]}):
            logger.info(f"{employee} | {att_date} | SKIP: Attendance already exists.")
            continue

        ins = [log for log in day_logs if log.log_type == "IN"]
        for first_in in ins:
            matched = _match_shift_window(first_in.time, att_date, windows_cfg)
            if not matched:
                logger.info(f"{employee} | {att_date} | OFFSHIFT IN")
                _mark_offshift(ins, employee, att_date)
                continue

            label, start, end, target_hours = matched
            start_dt = datetime.combine(att_date, start)
            end_dt = datetime.combine(att_date, end)
            if end <= start:
                end_dt += timedelta(days=1)

            valid_outs = [log for log in logs if log.log_type == "OUT" and first_in.time < log.time <= end_dt + timedelta(hours=12)]
            if not valid_outs:
                logger.warning(f"{employee} | {att_date} | {label} | FAILED: No valid OUT found.")
                continue
            last_out = valid_outs[-1]

            hours = (last_out.time - first_in.time).total_seconds() / 3600
            status, comment, late_entry, early_exit = _evaluate_shift_performance(
                employee, att_date, first_in, last_out, start_dt, end_dt, target_hours, hours
            )

            overtime_hours = _calculate_overtime(last_out.time, end_dt)

            _create_attendance(
                employee, att_date, first_in, last_out,
                hours, late_entry, early_exit, overtime_hours, status, matched, comment
            )
            break

    _handle_orphan_logs(employee, logs)

# HELPER FUNCTIONS
def _match_shift_window(checkin_time, att_date, windows_cfg):
    for label, start, end, target_hours in windows_cfg.get("all", []):
        if _in_matches_window(checkin_time, att_date, start):
            return label, start, end, target_hours
    return None

def _evaluate_shift_performance(employee, att_date, first_in, last_out, start_dt, end_dt, target_hours, hours):
    status = "Present"
    comment = None
    late_entry = first_in.time > (start_dt + timedelta(minutes=GRACE_MINUTES))
    early_exit = last_out.time < (end_dt - timedelta(minutes=GRACE_MINUTES))

    if hours < (target_hours / 2):
        status = "Half Day"
        comment = "Marked Half Day: Working hours less than Shift Hours."
        logger.info(f"{employee} | {att_date} | Under 50% Rule applied. Skipping grace check.")
    elif late_entry or early_exit:
        current_count = frappe.db.get_value("Employee", employee, "monthly_grace_count") or 0
        new_count = current_count + 1
        frappe.db.set_value("Employee", employee, "monthly_grace_count", new_count)

        if new_count > 3:
            status = "Half Day"
            comment = "Marked Half Day: Grace limit exceeded."
        else:
            comment = (f"Grace counter increased: Due to grace violation on {att_date}.")
        logger.info(f"{employee} | {att_date} | GRACE TRIGGERED: New Count = {new_count}")

    return status, comment, late_entry, early_exit

def _calculate_overtime(last_out_time, end_dt):
    ot_limit = end_dt + timedelta(minutes=GRACE_MINUTES)
    if last_out_time > ot_limit:
        return round((last_out_time - ot_limit).total_seconds() / 3600, 2)
    return 0

def _handle_orphan_logs(employee, logs):
    now = datetime.now()
    for log in logs:
        log_date = getdate(log.time)
        if (now - log.time).total_seconds() > 48 * 3600:
            if frappe.db.exists("Attendance", {"employee": employee, "attendance_date": log_date, "docstatus": ["<", 2]}):
                continue

            logger.info(f"{employee} | {log_date} | Marking Absent due to orphan log")
            _create_attendance(
                employee, log_date, None, None,
                hours=0, late=False, early=False,
                ot=0, status="Absent", matched=None,
                comment="Marked Absent: Orphan log older than 48 hours."
            )
        else:
            logger.info(f"{employee} | {log_date} | Skipping orphan log: Within 48 hours window")

def _in_matches_window(checkin_time, att_date, shift_start_time):
    shift_start_dt = datetime.combine(att_date, shift_start_time)
    return (shift_start_dt - timedelta(hours=0.5)) <= checkin_time <= (shift_start_dt + timedelta(hours=0.5))

def _create_attendance(employee, att_date, first_in, last_out, hours, late, early, ot, status, matched, comment):
    if matched is None:
        label = "N/A"
    else:
        label, start, end, target_hours = matched
    att = frappe.new_doc("Attendance")
    try:
        att.update({
            "employee": employee,
            "attendance_date": att_date,
            "status": status,
            "working_hours": round(hours, 2) if hours else 0,
            "overtime_hours": ot if ot else 0,
            "in_time": first_in.time if first_in else None,
            "out_time": last_out.time if last_out else None,
            "shift": SHIFT_NAME,
            "shift_window": label,
            "late_entry": 1 if late else 0,
            "early_exit": 1 if early else 0,
        })

        att.insert(ignore_permissions=True)
        att.submit()
        if comment:
            att.add_comment("Comment", comment)

        logger.info(f"Attendance Created: {employee} on {att_date}")
        # Link check-ins using first_in and last_out
        if first_in and last_out:
            frappe.db.set_value("Employee Checkin", {"name": ["in", [first_in.name, last_out.name]]}, "attendance", att.name)
    except Exception as e:
        logger.error(f"Error creating attendance for {employee}: {str(e)}")

def _mark_offshift(logs, employee, att_date):
    # Just log it or set a remark on the checkin
    for log in logs:
        frappe.db.set_value("Employee Checkin", log.name, "offshift", 1)
        frappe.get_doc("Employee Checkin", log.name).add_comment(
            "Comment",
            f"Off-shift: IN did not match any shift window on {att_date}."
        )
        logger.info(f"{employee} | {att_date} | Off-shift log marked.")
