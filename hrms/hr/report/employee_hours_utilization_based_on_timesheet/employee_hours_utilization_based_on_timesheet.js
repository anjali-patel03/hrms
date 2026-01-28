frappe.query_reports["Employee Hours Utilization Based On Timesheet"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1,
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            reqd: 1,
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.now_date(),
            reqd: 1,
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
            fieldname: "project",
            label: __("Project"),
            fieldtype: "Link",
            options: "Project",
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
