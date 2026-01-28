import frappe
from frappe import _
#import request

@frappe.whitelist(allow_guest=True)
def custom_logout(usr):
    """
    Custom API to log out a specific user by email.
    This API works similar to /api/method/login but for logging out.
    """
    #if not frappe.session.user == "Administrator":
        #frappe.throw(_("Only Administrator can log out other users."))

    if not frappe.db.exists("User", usr):
        frappe.throw(_("User does not exist."))

    # Clear all sessions for the specified user
    try:
        #frappe.sessions.clear_sessions(user=usr)
        #user_sessions = frappe.db.get_all(
        #    "Sessions",
        #    filters={"user": user_email},
        #    fields=["sid", "lastupdate"],
        #    order_by="lastupdate desc"
        #)
        #user_sid = user_sessions[0].sid
        frappe.local.response['message'] = {
            "status": "success",
            "link": frappe.utils.get_url("/api/method/logout")
        }
    except Exception as e:
        frappe.local.response['message'] = {
            "status": "failed",
            "message": f"Error: {str(e)}" 
        }


    #return {"status": "success", "message": f"User {user_email} has been logged out."}
