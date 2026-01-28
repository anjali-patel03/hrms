import frappe
from frappe.core.doctype.user.user import User

class CustomUser(User):

    def has_permission(self, *args, **kwargs):
        perm = super().has_permission(*args, **kwargs)
        if not perm:
            return False

        current_user = frappe.session.user

        #print(">>> CustomUser loaded")
        #frappe.log_error("CustomUser override active", "DEBUG")

        # Users with full visibility
        if current_user in ["Administrator", "Guest", "hr_admin@bmcinternal.com", "admin@bmcinternal.com"]:
            return True

        current_user_org = frappe.db.get_value("User", current_user, "company")

        if not current_user_org:
            return False

        target_user_org = self.company

        if not target_user_org:
            return False

        return target_user_org == current_user_org

def user_permission_query(user: str) -> str:
    if user in ["Administrator", "Guest", "hr_admin@bmcinternal.com", "admin@bmcinternal.com"]:
        # frappe.log_error(f"Permission query: full access user = {user}", "DEBUG")
        return ""

    current_company = frappe.db.get_value("User", user, "company")

    if not current_company:
        # frappe.log_error(f"Permission query: user {user} has no company, blocking all", "DEBUG")
        return "1 = 0"

    escaped_company = frappe.db.escape(current_company)

    condition = f"""
        ifnull(company, '') != ''
        AND company = {escaped_company}
    """
   # frappe.log_error(f"Permission query for {user}: {condition}", "DEBUG")
    return condition
