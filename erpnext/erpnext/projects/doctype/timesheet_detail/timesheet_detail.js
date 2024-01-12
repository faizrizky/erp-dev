frappe.ui.form.on("Timesheet Detail", {
	onload: function (frm) {
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Employee",
				filters: { user_id: frappe.session.user },
				fieldname: ["employee_name"],
			},
			callback: function (response) {
				alert(response);
				if (
					response &&
					response.message &&
					response.message.employee_name
				) {
					var employeeFullName = response.message.employee_name;
					frm.set_value("employee", employeeFullName);
				} else {
					frappe.msgprint("Employee not found!");
				}
			},
		});
	},
});
