frappe.query_reports["Employee Leave Balance"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 1,
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            reqd: 1,
        },
        {
            label: __("Company"),
            fieldname: "company",
            fieldtype: "Link",
            options: "Company",
            reqd: 1,
            default: frappe.defaults.get_user_default("Company"),
        },
        {
            fieldname: "department",
            label: __("Department"),
            fieldtype: "Link",
            options: "Department",
        },
        {
            fieldname: "employee",
            label: __("Employee"),
            fieldtype: "Link",
            options: "Employee",
        },
        {
            fieldname: "employee_status",
            label: __("Employee Status"),
            fieldtype: "Select",
            options: [
                "",
                { value: "Active", label: __("Active") },
                { value: "Inactive", label: __("Inactive") },
                { value: "Suspended", label: __("Suspended") },
                { value: "Left", label: __("Left", null, "Employee") },
            ],
            default: "Active",
        },
        {
            fieldname: "consolidate_leave_types",
            label: __("Consolidate Leave Types"),
            fieldtype: "Check",
            default: 1,
            depends_on: "eval: !doc.employee",
        },
    ],

    onload: function(report) {
        let company_filter = report.filters.find(f => f.fieldname === "company");

        if (!company_filter) return;

        // Auto-select company if only 1 exists
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Company",
                limit_page_length: 2
            },
            callback: function(r) {
                let selected_company = frappe.defaults.get_user_default("Company");

                if (r.message && r.message.length === 1) {
                    selected_company = r.message[0].name;
                    company_filter.set_input(selected_company);
                    company_filter.refresh();
                }

                // Now call get_leave_period with the selected company
                const today = frappe.datetime.now_date();
                frappe.call({
                    type: "GET",
                    method: "hrms.hr.utils.get_leave_period",
                    args: {
                        from_date: today,
                        to_date: today,
                        company: selected_company
                    },
                    freeze: true,
                    callback: function(data) {
                        if (data.message && data.message.length > 0) {
                            frappe.query_report.set_filter_value("from_date", data.message[0].from_date);
                            frappe.query_report.set_filter_value("to_date", data.message[0].to_date);
                        }
                    }
                });
            }
        });
    }
};
