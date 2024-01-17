// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Support Ticket", {
	refresh: function (frm) {
		frm.set_df_property("subject", "hidden", frm.is_new() ? 0 : 1);
		frm.set_df_property("status", "hidden", frm.is_new() ? 1 : 0);
		frm.set_df_property("naming_series", "hidden", frm.is_new() ? 0 : 1);
	},

	onload: function (frm) {
		// Fetch the current user's employee information
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Employee",
				filters: { user_id: frappe.session.user },
				fieldname: ["employee_name", "department"],
			},
			callback: function (response) {
				if (
					response &&
					response.message &&
					response.message.employee_name &&
					response.message.department
				) {
					if (frm.doc.employee == null) {
						var employeeFullName = response.message.employee_name;
						var employeeDivision = response.message.department;
						frm.set_value("employee", employeeFullName);
						frm.set_value("division", employeeDivision);
					}
				} else {
					if (frappe.session.user != "Administrator") {
						frappe.throw({
							message:
								"You are not registered as an Employee yet. Please contact your supervisor to complete the registration process immediately.",
							title: "Permission Denied",
						});
					}
				}
			},
		});
	},
});
