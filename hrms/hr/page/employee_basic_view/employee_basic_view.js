frappe.pages['employee_basic_view'].on_page_load = function(wrapper) {
    frappe.call({
        method: "frappe.client.get_value",
        args: {
            doctype: "Employee",
            filters: {
                user_id: frappe.session.user
            },
            fieldname: "name"
        },
        callback: function(r) {
            if (r && r.message && r.message.name) {
                const employee_id = r.message.name;
                // Redirecting to the workspace/route with a tab anchor
                frappe.set_route("app", "employee", employee_id);
                // Optional: delay before applying the tab hash
                setTimeout(() => {
                    window.location.hash = "tab=connections";
                }, 100);
            } else {
                frappe.msgprint("Employee record not found for the current user.");
            }
        }
    });
};
