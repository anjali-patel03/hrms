frappe.query_reports["Employees working on a holiday"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.year_start(),
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.year_end(),
        },
        {
            fieldname: "holiday_list",
            label: __("Holiday List"),
            fieldtype: "Link",
            options: "Holiday List",
        },
        {
            fieldname: "department",
            label: __("Department"),
            fieldtype: "Link",
            options: "Department",
        },
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            reqd: 1,
            default: frappe.defaults.get_user_default("Company"),
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
                    company_filter.df.default = company;  // preserves default
                    company_filter.refresh();
                }
            }
        });
    }
};
