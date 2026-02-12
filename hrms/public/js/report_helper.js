window.auto_select_company = function (report) {
    if (!report) return;

    let company_filter = report.filters.find(f => f.fieldname === "company");
    if (!company_filter) return;

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
        }
    });
};
