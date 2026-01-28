frappe.query_reports["Employee Leave Balance Summary"] = {
    filters: [
        {
            fieldname: "date",
            label: __("Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.now_date(),
        },
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            reqd: 1,
            default: frappe.defaults.get_user_default("Company"),
        },
        {
            fieldname: "employee",
            label: __("Employee"),
            fieldtype: "Link",
            options: "Employee",
        },
        {
            fieldname: "department",
            label: __("Department"),
            fieldtype: "Link",
            options: "Department",
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
                { value: "Left", label: __("Left") },
            ],
            default: "Active",
        },
    ],

    onload: function(report) {
        let company_filter = report.get_filter("company");

        // Auto-select company if only one exists
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Company",
                limit_page_length: 2
            },
            callback: function(r) {
                if (r.message && r.message.length === 1) {
                    let company = r.message[0].name;
                    company_filter.set_input(company);
                    company_filter.df.default = company;
                    company_filter.refresh();
                }
            }
        });
    }
};
