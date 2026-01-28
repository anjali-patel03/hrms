# in your custom app: myapp/api.py

import frappe
from frappe import _
from frappe.utils import cint

@frappe.whitelist(allow_guest=True)
def auto_login_user(email, password, redirect_url=None):
    try:
        user = frappe.get_doc("User", email)
        if user and user.check_password(password):
            frappe.local.login_manager.login_as(user.name)
            
            # If redirect URL is provided, redirect to it
            if redirect_url:
                frappe.local.response["type"] = "redirect"
                frappe.local.response["location"] = redirect_url
            else:
                return {"status": "success", "message": _("Logged In")}
        else:
            return {"status": "error", "message": _("Invalid Credentials")}
    except frappe.DoesNotExistError:
        return {"status": "error", "message": _("User does not exist")}
