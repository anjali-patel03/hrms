frappe.query_reports["Shift Attendance"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_start(),
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_end(),
        },
        {
            fieldname: "employee",
            label: __("Employee"),
            fieldtype: "Link",
            options: "Employee",
        },
        {
            fieldname: "shift",
            label: __("Shift Type"),
            fieldtype: "Link",
            options: "Shift Type",
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
        {
            fieldname: "late_entry",
            label: __("Late Entry"),
            fieldtype: "Check",
        },
        {
            fieldname: "early_exit",
            label: __("Early Exit"),
            fieldtype: "Check",
        },
        {
            fieldname: "consider_grace_period",
            label: __("Consider Grace Period"),
            fieldtype: "Check",
            default: 1,
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
    },

    formatter: (value, row, column, data, default_formatter) => {
        value = default_formatter(value, row, column, data);
        if (
            (column.fieldname === "in_time" && data.late_entry) ||
            (column.fieldname === "out_time" && data.early_exit)
        ) {
            value = `<span style='color:red!important'>${value}</span>`;
        }
        return value;
    },
};
