# hrms/utils/4hr_scheduler_job.py
import frappe
from frappe.utils import getdate
from datetime import datetime, time, timedelta
from collections import defaultdict
import logging
from logging.handlers import RotatingFileHandler
import os

GRACE_MINUTES = 15
MIN_HALF_DAY_HOURS = 2
SHIFT_NAME = "4_hr_shift"

# Logger setup
LOG_FILE = os.path.join(
    frappe.get_site_path(), "logs", "4hr_attendance_scheduler.log"
)

logger = logging.getLogger("4hr_attendance_scheduler")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=7
    )
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def run_daily_4hr_attendance():
    today = getdate()
    start_date = today - timedelta(days=3)
    end_date = today

    logger.info("=" * 80)
    logger.info(f"START scheduler | window={start_date} → {end_date}")
    logger.info("=" * 80)

    checkins = frappe.get_all(
        "Employee Checkin",
        filters={
            "attendance": ["is", "not set"],
            "shift": SHIFT_NAME,
            "time": ["between", [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]],
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
            _process_employee_4hr(employee, logs, emp_master)
            frappe.db.commit()

        except Exception:
            frappe.db.rollback()
            frappe.log_error(frappe.get_traceback(), f"4hr Scheduler Failed: {employee}")
    logger.info("END scheduler")
    logger.info("=" * 80)


def _process_employee_4hr(employee, logs, emp_master):
    logs.sort(key=lambda x: x.time)

    daily_logs = defaultdict(list)
    for l in logs:
        daily_logs[getdate(l.time)].append(l)

    for att_date, day_logs in daily_logs.items():
        if frappe.db.exists(
            "Attendance",
            {"employee": employee, "attendance_date": att_date, "docstatus": ["<", 2]},
        ):
            continue

        logger.info(f"Processing {employee} on {att_date}")

        ins = [l for l in day_logs if l.log_type == "IN"]
        outs = [l for l in day_logs if l.log_type == "OUT"]

        if not ins or not outs:
            continue

        first_in = ins[0]
        last_out = outs[-1]

        window = _get_applicable_window(employee, att_date, first_in.time)

        if not window:
            checkin_names = [l.name for l in day_logs]

            frappe.db.set_value(
                "Employee Checkin",
                {"name": ["in", checkin_names]},
                "offshift",
                1,
            )

            comment = (
                f"Marked Off-shift by system. "
                f"IN time {first_in.time} did not match any configured shift window."
            )

            for chk_name in checkin_names:
                frappe.get_doc("Employee Checkin", chk_name).add_comment(
                "Comment", comment
            )
            continue

        # Calculate working hours
        working_hours = (last_out.time - first_in.time).total_seconds() / 3600
        overtime_hours = _calculate_overtime(working_hours, window)

        # Grace-aware late / early check
        start_with_grace = datetime.combine(att_date, window["start"]) + timedelta(minutes=GRACE_MINUTES)
        end_with_grace = datetime.combine(att_date, window["end"]) - timedelta(minutes=GRACE_MINUTES)

        first_in_dt = first_in.time if isinstance(first_in.time, datetime) else datetime.combine(att_date, first_in.time)
        last_out_dt = last_out.time if isinstance(last_out.time, datetime) else datetime.combine(att_date, last_out.time)

        late_entry = first_in_dt > start_with_grace
        early_exit = last_out_dt < end_with_grace

        #late_entry = first_in.time > start_with_grace
        #early_exit = last_out.time < end_with_grace

        # Monthly grace violation logic
        monthly_count = frappe.db.get_value(
            "Employee", employee, "monthly_grace_count"
        ) or 0

        if late_entry or early_exit:
            monthly_count += 1
            frappe.db.set_value(
                "Employee", employee, "monthly_grace_count", monthly_count
            )

        # Attendance status decision
        comment = None
        status = "Present"

        # Less than 2 hours --> Half Day
        if working_hours < MIN_HALF_DAY_HOURS:
            status = "Half Day"
            comment = "Marked as Half Day due to insufficient working hours for the assigned shift."

        # Grace violation more than 3 times --> Half Day
        if monthly_count > 3:
            status = "Half Day"
            comment = "Marked as Half Day due to exceeding the allowed number of grace period violations for the month."

        # Create Attendance
        att = frappe.new_doc("Attendance")
        emp = emp_master.get(employee)

        att.update({
            "employee": employee,
            "attendance_date": att_date,
            "status": status,
            "working_hours": round(working_hours, 2),
            "in_time": first_in.time,
            "out_time": last_out.time,
            "company": emp.company if emp else None,
            "department": emp.department if emp else None,
            "shift": SHIFT_NAME,
            "shift_window": window["label"],
            "overtime_hours": round(overtime_hours, 2),
            "late_entry": late_entry,
            "early_exit": early_exit,
        })

        logger.info(
            f"{employee} | {att_date} | {status} | {working_hours}h | {window['label']}"
        )

        try:
            att.insert(ignore_permissions=True)
            att.submit()
            if comment:
                att.add_comment("Comment", comment)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"4hr Scheduler Failed: {employee}")

        # Link checkins to attendance
        frappe.db.set_value(
            "Employee Checkin",
            {"name": ["in", [first_in.name, last_out.name]]},
            "attendance",
            att.name,
        )


# helpers
def _get_applicable_window(employee, att_date, in_time):
    weekday = att_date.weekday()  # Sunday

    # Normalize in_time to datetime
    t_dt = in_time if isinstance(in_time, datetime) else datetime.combine(att_date, in_time)

#    SPECIAL_WINDOW = {
#        "EMP-00012": (time(9,0), time(12,30)),  # Rutuja
#        "EMP-00045": (time(10,0), time(14,00)), # Another employee
#    }

    RUTUJA_ID = "HR-EMP-02637"
    if employee == RUTUJA_ID:
        return _window("Late Morning", time(9,0), time(12,30))

#    if employee in SPECIAL_WINDOW:yyyyyyy
#        start, end = SPECIAL_WINDOW[employee]
#        return _window("Special", start, end)

    if weekday == 6:  # Sunday
        windows = [
            _window("Late Morning", time(9, 0), time(13, 0)),
            _window("Afternoon", time(16, 0), time(20, 0)),
        ]
    else:
        windows = [
            _window("Morning", time(7, 0), time(11, 0)),
            _window("Late Morning", time(11, 0), time(15, 0)),
        ]

    for w in windows:
        start_dt = datetime.combine(att_date, w["start"]) - timedelta(minutes=GRACE_MINUTES)
        end_dt = datetime.combine(att_date, w["end"]) + timedelta(minutes=GRACE_MINUTES)
        if start_dt <= t_dt <= end_dt:
            return w

    return None

def _window(label, start, end):
    return {
        "label": label,
        "start": start,
        "end": end,
        "duration_hours": (datetime.combine(datetime.today(), end)
                           - datetime.combine(datetime.today(), start)).seconds / 3600
    }

def _time_with_grace(t, start, end, att_date):
    start_dt = datetime.combine(att_date, start) - timedelta(minutes=GRACE_MINUTES)
    end_dt = datetime.combine(att_date, end) + timedelta(minutes=GRACE_MINUTES)
    t_dt = datetime.combine(att_date, t) if isinstance(t, time) else t
    return start_dt <= t_dt <= end_dt

def _is_within_grace(in_time, out_time, window):
    start_limit = datetime.combine(in_time.date(), window["start"]) - timedelta(minutes=GRACE_MINUTES)
    end_limit = datetime.combine(out_time.date(), window["end"]) + timedelta(minutes=GRACE_MINUTES)
    return start_limit <= in_time <= end_limit and start_limit <= out_time <= end_limit


def _calculate_overtime(working_hours, window):
    regular_cap = window["duration_hours"] + (GRACE_MINUTES / 60)
    return max(0, working_hours - regular_cap)
