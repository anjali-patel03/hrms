# hrms/overrides/employee_checkin.py
import frappe
from hrms.hr.doctype.employee_checkin.employee_checkin import EmployeeCheckin


class CustomEmployeeCheckin(EmployeeCheckin):

    def before_insert(self):
        # Hard guarantee: no attendance on INSERT
        self.attendance = None

    def validate(self):
        # FIRST: run ALL original logic
        super().validate()

        # THEN: enforce your rule
        if self.is_new():
            self.attendance = None

    def onload(self):
        # UI hygiene only
        if self.is_new():
            self.attendance = None
