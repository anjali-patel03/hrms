import frappe
import json

EXEMPT_USERS = ["Administrator", "Guest", "hr_admin@bmcinternal.com"]

@frappe.whitelist()
def get_filtered_users(doctype=None, fields=None, filters=None,
                       start=0, page_length=20, order_by=None, **kwargs):

    # LOG for diagnostics
    frappe.log_error(
        f"Custom User Filter Triggered by {frappe.session.user}",
        "DEBUG-USER-FILTER"
    )

    filters = json.loads(filters) if filters else []
    field_list = json.loads(fields) if fields else ["name"]

    current_user = frappe.session.user

    # Exemption condition
    if current_user in EXEMPT_USERS:
        frappe.log_error("Exempt user detected — returning all users", "DEBUG-USER-FILTER")
        return frappe.get_list(
            doctype,
            fields=field_list,
            filters=filters,
            limit_start=start,
            limit_page_length=page_length,
            order_by=order_by,
        )

    current_org = frappe.get_value("User", current_user, "company")

    # Only restrict normal users
    if current_org:
        filters.append(["company", "=", current_org])

    filters.append(["company", "!=", ""])

    frappe.log_error(
        f"Final Filters Applied: {filters}",
        "DEBUG-USER-FILTER"
    )

    return frappe.get_list(
        doctype,
        fields=field_list,
        filters=filters,
        limit_start=start,
        limit_page_length=page_length,
        order_by=order_by,
    )
