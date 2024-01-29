// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('SD Issue', {
	onload: function (frm) {
		if (
			frm.doc.task_issue !== undefined &&
			frm.doc.task_issue !== null &&
			frm.doc.task_issue !== ""
		) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Task",
					name: frm.doc.task_issue,
				},
				callback: function (r) {
					if (r.message) {
						console.log(r.message);
						var doc_task = r.message;
						var testingTableData = doc_task.testing_table;
						var testing_personel = [];

						for (var i = 0; i < testingTableData.length; i++) {
							var employeeName =
								testingTableData[i].employee_name;
							testing_personel.push(employeeName);
						}

						if (testing_personel.includes(frm.doc.employee)) {
							frm.set_df_property("status", "read_only", 0);
						} else {
							frm.set_df_property("status", "read_only", 1);
						}
					}
				},
			});
		} else {
			frm.set_df_property("status", "read_only", 1);
		}

		// Fetch the current user's employee information
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Employee",
				filters: { user_id: frappe.session.user },
				fieldname: ["employee_name"],
			},
			callback: function (response) {
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

	refresh(frm) {
		if (frm.doc.task_issue)
			frm.set_df_property('task_issue', 'read_only', 1)
		if (frm.doc.first_responded_on) {
			frm.set_df_property('first_responded_on', 'read_only', 1)
		} else {
			frm.set_df_property('first_responded_on', 'read_only', 0)
		}
		if (frm.doc.contact) {
			frm.set_df_property('contact', 'read_only', 1)
		} else {
			frm.set_df_property('contact', 'read_only', 0)
		}
		if (frm.doc.resolved_time) {
			frm.set_df_property('resolved_time', 'read_only', 1)
		} else {
			frm.set_df_property('resolved_time', 'read_only', 0)
		}

	}
	// }
});
