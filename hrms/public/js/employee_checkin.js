// public/js/employee_checkin.js

frappe.ui.form.on("Employee Checkin", {
    onload(frm) {
        if (frm.is_new()) {
            hide_attendance(frm);
        }
    },

    refresh(frm) {
        if (frm.is_new()) {
            hide_attendance(frm);
        }
    }
});

function hide_attendance(frm) {
    // Clear value defensively
    frm.set_value("attendance", null);

    // Hide from UI completely
    frm.set_df_property("attendance", "hidden", 1);
    frm.set_df_property("attendance", "read_only", 1);

    // Force re-render (important)
    frm.refresh_field("attendance");
}
