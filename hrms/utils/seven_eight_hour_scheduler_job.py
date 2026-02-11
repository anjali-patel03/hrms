import frappe
from frappe.utils import getdate
from datetime import datetime, time, timedelta
from collections import defaultdict
import logging
from logging.handlers import RotatingFileHandler
import os

SHIFT_NAME = "7_8_HOUR_SHIFT"
LOOKBACK_DAYS = 3

# LOGGER SETUP
LOG_FILE = os.path.join(
    frappe.get_site_path(), "logs", "7_8hr_attendance_scheduler.log"
)

logger = logging.getLogger("7_8hr_attendance_scheduler")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = RotatingFileHandler(LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=7)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

EMPLOYEE_SHIFT_WINDOWS = {
    # PRANALI GANESH SANGLE, POOJA BHARATKISHOR PATWA
    "HR-EMP-12615": {
        "weekday": [
            ("Morning Shift", time(9, 0), time(16, 0)),
            ("Evening Shift", time(16, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
    },
    "HR-EMP-12591": {  # same as above
        "weekday": [
            ("Morning Shift", time(9, 0), time(16, 0)),
            ("Evening Shift", time(16, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
    },

    # SAI BHGWAN SATAM
    "HR-EMP-04920": {
        "weekday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
    },
    # SAGAR SHRIPAL KHARAT
    "HR-EMP-05832": {
        "weekday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
    },
    # RAJVI ASHOK SOLKAR
    "HR-EMP-04946": {
        "weekday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
    },
    # JYOTSNA BALIRAM SAPALE
    "HR-EMP-05835": {
        "weekday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
    },
    # SONALI AJAY BHOSLE
    "HR-EMP-05842": {
        "weekday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
    },

    # ANITA M AYYOLLU
    "HR-EMP-04926": {
        "weekday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
    },
    # SHWETA SURAJ KONDVILKAR
    "HR-EMP-08081": {
        "weekday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
    },

    # CONT. RA / TEL OPERATOR
    "HR-EMP-12579": {  # AJAY SUBHASH CHANDANE
        "weekday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
    },
    "HR-EMP-12577": {  # SIDDHESH AVINASH WAGHMARE
        "weekday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
    },
    "HR-EMP-12574": {  # SIDDHESH SANJAY JADHAV
        "weekday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(7, 0), time(15, 0)),
            ("Evening Shift", time(15, 0), time(23, 0)),
            ("Night Shift", time(23, 0), time(7, 0)),
        ],
    },

    # TRUPTI SHIVAJI HAKE
    "HR-EMP-12459": {
        "weekday": [
            ("Morning Shift", time(9, 0), time(16, 0)),
            ("Evening Shift", time(16, 0), time(21, 0)),
            ("Night Shift", time(21, 0), time(9, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(9, 0), time(16, 0)),
            ("Evening Shift", time(16, 0), time(21, 0)),
            ("Night Shift", time(21, 0), time(9, 0)),
        ],
    },
    # DEEPALI SUSHANT RAUT
    "HR-EMP-12458": {
        "weekday": [
            ("Morning Shift", time(9, 0), time(16, 0)),
            ("Evening Shift", time(16, 0), time(21, 0)),
            ("Night Shift", time(21, 0), time(9, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(9, 0), time(16, 0)),
            ("Evening Shift", time(16, 0), time(21, 0)),
            ("Night Shift", time(21, 0), time(9, 0)),
        ],
    },
    # SWAMIL DEVAJI SAKPAL
    "HR-EMP-12457": {
        "weekday": [
            ("Morning Shift", time(9, 0), time(16, 0)),
            ("Evening Shift", time(16, 0), time(21, 0)),
            ("Night Shift", time(21, 0), time(9, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(9, 0), time(16, 0)),
            ("Evening Shift", time(16, 0), time(21, 0)),
            ("Night Shift", time(21, 0), time(9, 0)),
        ],
    },
    # IRFAN NIJAM SHAIKH
    "HR-EMP-12456": {
        "weekday": [
            ("Morning Shift", time(9, 0), time(16, 0)),
            ("Evening Shift", time(16, 0), time(21, 0)),
            ("Night Shift", time(21, 0), time(9, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(9, 0), time(16, 0)),
            ("Evening Shift", time(16, 0), time(21, 0)),
            ("Night Shift", time(21, 0), time(9, 0)),
        ],
    },

    # SHASHI DATTARAM VELEKAR
    "HR-EMP-12455": {
        "weekday": [
            ("Morning Shift", time(9, 30), time(16, 30)),
            ("Evening Shift", time(14, 0), time(21, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(9, 30), time(16, 30)),
            ("Evening Shift", time(14, 0), time(21, 0)),
        ],
    },

    # Harsha Manish Saraf
    "HR-EMP-12454": {
        "weekday": [
            ("Morning Shift", time(8, 30), time(16, 30)),
            ("Evening Shift", time(10, 0), time(18, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(8, 30), time(16, 30)),
            ("Evening Shift", time(10, 0), time(18, 0)),
        ],
    },
    # Pradnya Sunil Ghanekar
    "HR-EMP-12453": {
        "weekday": [
            ("Morning Shift", time(8, 30), time(16, 30)),
            ("Evening Shift", time(10, 0), time(18, 0)),
        ],
        "sunday": [
            ("Morning Shift", time(8, 30), time(16, 30)),
            ("Evening Shift", time(10, 0), time(18, 0)),
        ],
    },

    # Siddhesh Sanjay Karkar
    "HR-EMP-12439": {
        "weekday": [
            ("Morning Shift", time(8, 30), time(16, 30)),
        ],
        "sunday": [
            ("Morning Shift", time(8, 30), time(16, 30)),
        ],
    },
}

# GRACE CONSTANTS
IN_MATCH_BEFORE_MIN = 30
IN_MATCH_AFTER_MIN = 60
GRACE_MIN = 15
MAX_MONTHLY_GRACE = 3

# MAIN SCHEDULER
def run_daily_7_8hr_attendance():
    today = getdate()
    start_date = today - timedelta(days=LOOKBACK_DAYS)

    logger.info("=" * 80)
    logger.info(f"START 7–8 HR scheduler | window={start_date} → {today}")
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
        frappe.db.begin()
        try:
            logger.info(f"PROCESSING EMPLOYEE {employee} | logs={len(logs)}")
            _process_employee(employee, logs)
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            logger.exception(f"FAILED employee {employee}")

    logger.info("END scheduler")
    logger.info("=" * 80)

# EMPLOYEE PROCESSING
def _process_employee(employee, logs):
    logs.sort(key=lambda x: x.time)

    daily = defaultdict(list)
    for l in logs:
        daily[getdate(l.time)].append(l)

    windows_cfg = EMPLOYEE_SHIFT_WINDOWS.get(employee)
    if not windows_cfg:
        logger.info(f"{employee} | No shift config")
        return

    for att_date, day_logs in daily.items():

        if frappe.db.exists("Attendance", {
            "employee": employee,
            "attendance_date": att_date,
            "docstatus": ["<", 2],
        }):
            logger.info(f"{employee} | {att_date} | Attendance already exists")
            continue

        ins = sorted([l for l in day_logs if l.log_type == "IN"], key=lambda x: x.time)
        outs = sorted([l for l in logs if l.log_type == "OUT"], key=lambda x: x.time)

        logger.info(
            f"{employee} | {att_date} | INs={len(ins)} OUTs={len(outs)}"
        )

        if not ins:
            continue

        first_in = ins[0]

        weekday_key = "sunday" if att_date.weekday() == 6 else "weekday"
        windows = windows_cfg.get(weekday_key, [])

        matched = None
        for label, start, end in windows:
            if _in_matches_window(first_in.time, att_date, start):
                matched = (label, start, end)
                break

        if not matched:
            logger.info(f"{employee} | {att_date} | OFFSHIFT IN")
            _mark_offshift(ins, employee, att_date)
            continue

        label, start, end = matched
        start_dt = datetime.combine(att_date, start)
        end_dt = datetime.combine(att_date, end)
        if end <= start:
            end_dt += timedelta(days=1)

        # Extend OUT log window by 4 hours after shift end
        valid_outs = [
            o for o in outs
            if first_in.time < o.time <= end_dt + timedelta(hours=4)
        ]

        if not valid_outs:
            logger.info(f"{employee} | {att_date} | No valid OUT")
            continue

        last_out = valid_outs[-1]

        grace_violation = False
        comment = None

        # LATE ENTRY
        late_minutes = (first_in.time - (start_dt + timedelta(minutes=GRACE_MIN))).total_seconds() / 60
        if late_minutes > 0:
            grace_violation = True
            logger.info(f"{employee} | {att_date} | Late Entry {late_minutes:.1f} min")

        # EARLY EXIT
        early_minutes = ((end_dt - timedelta(minutes=GRACE_MIN)) - last_out.time).total_seconds() / 60
        if early_minutes > 0:
            grace_violation = True
            logger.info(f"{employee} | {att_date} | Early Exit {early_minutes:.1f} min")

        late_entry = first_in.time > (start_dt + timedelta(minutes=GRACE_MIN))
        early_exit = last_out.time < (end_dt - timedelta(minutes=GRACE_MIN))

        if grace_violation:
            exceeded = _increment_monthly_grace(employee, att_date)
            if exceeded:
                status = "Half Day"
                comment = "Marked Half Day: Grace limit exceeded."
            else:
                comment = (f"Grace counter increased: Due to grace violation on {att_date}.")
        else:
            status = "Present"

        # WORK HOURS
        worked_hours = (last_out.time - first_in.time).total_seconds() / 3600
        shift_hours = (end_dt - start_dt).total_seconds() / 3600

        if worked_hours < (shift_hours - 0.5):
            status = "Half Day"
            comment = "Marked Half Day: Working hours less than Shift Hours."

        # OVERTIME
        overtime_hours = 0
        overtime_start = end_dt + timedelta(minutes=GRACE_MIN)
        if last_out.time > overtime_start:
            overtime_hours = round(
                (last_out.time - overtime_start).total_seconds() / 3600, 2
            )

        _create_attendance(
            employee, att_date, first_in, last_out,
            worked_hours, late_entry, early_exit, overtime_hours, status, matched, comment
        )

    # HANDLE ORPHAN LOGS
    now = datetime.now()
    for log in logs:
        log_date = getdate(log.time)
        if (now - log.time).total_seconds() > 48 * 3600:  # Check if log is older than 48 hours
            if frappe.db.exists("Attendance", {
                "employee": employee,
                "attendance_date": log_date,
                "docstatus": ["<", 2],
            }):
                continue

            logger.info(f"{employee} | {log_date} | Marking Absent due to orphan log")
            _create_attendance(
                employee, log_date, None, None,
                worked_hours=0, late_entry=False, early_exit=False,
                overtime_hours=0, status="Absent", matched=None,
                comment=(f"Marked Absent: IN/OUT Logs missing for the date {log_date}")
            )
        else:
            logger.info(f"{employee} | {log_date} | Skipping orphan log: Within 48 hours window")

# HELPERS
def _in_matches_window(in_time, date, start):
    start_dt = datetime.combine(date, start)
    early = start_dt - timedelta(minutes=IN_MATCH_BEFORE_MIN)
    late = start_dt + timedelta(minutes=IN_MATCH_AFTER_MIN)
    logger.info(f"IN MATCH WINDOW {early} → {late} | IN={in_time}")
    return early <= in_time <= late

def _increment_monthly_grace(employee, date):
    emp = frappe.get_doc("Employee", employee)
    count = emp.monthly_grace_count or 0

    if count > MAX_MONTHLY_GRACE:
        logger.info(f"{employee} | Grace limit exceeded")
        return True

    emp.monthly_grace_count = count + 1
    emp.save(ignore_permissions=True)

    logger.info(f"{employee} | Monthly grace incremented → {count + 1}")
    return False

def _create_attendance(employee, date, in_log, out_log, worked_hours, late_entry, early_exit, overtime_hours, status, matched, comment):
    if matched is None:
        label = "N/A"
    else:
        label, start, end = matched
    att = frappe.new_doc("Attendance")
    att.update({
        "employee": employee,
        "attendance_date": getdate(in_log.time) if in_log else date,
        "status": status,
        "in_time": in_log.time if in_log else None,
        "out_time": out_log.time if out_log else None,
        "working_hours": round(worked_hours, 2) if worked_hours else 0,
        "overtime_hours": overtime_hours if overtime_hours else 0,
        "shift": SHIFT_NAME,
        "shift_window": label,
        "late_entry": late_entry ,
        "early_exit": early_exit,
    })
    att.insert(ignore_permissions=True)
    att.submit()
    if comment:
        att.add_comment("Comment",comment)

    for log in (in_log, out_log):
        if log:
            frappe.db.set_value("Employee Checkin", log.name, "attendance", att.name)

    logger.info(
        f"ATT CREATED | {employee} | {date} | {status} | "
        f"WH={worked_hours:.2f} OT={overtime_hours:.2f}"
    )

def _mark_offshift(logs, employee, date):
    for l in logs:
        frappe.db.set_value("Employee Checkin", l.name, "offshift", 1)
        frappe.get_doc("Employee Checkin", l.name).add_comment(
            "Comment",
            f"Off-shift: IN did not match any 7–8 hr window on {date}"
        )
