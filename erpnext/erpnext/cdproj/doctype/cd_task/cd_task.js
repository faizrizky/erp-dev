// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext.projects");

document.validate_rename = function (value) {
	var regex = /-/g;

	if (this.frm.doc.status == "Completed") {
		frappe.throw({
			message: __(
				"Your Task status is {0}. You can't rename a Task while status is {0}. Please move your task to another status, then try to rename it.",
				["<b>" + this.frm.doc.status + "</b>"]
			),
			title: __("Invalid Task Name"),
		});
	}
	if (
		value.title.match(regex) !== null &&
		value.title.match(regex).length > 1
	) {
		frappe.throw({
			message: __(
				"{0} is using more than one hyphen (-). The maximum allowed hyphen (-) is one.",
				["<b>" + value.title + "</b>"]
			),
			title: __("Invalid Task Name"),
		});
	}
};

frappe.ui.form.on("CD Task", {
	setup: function (frm) {
		frm.make_methods = {
			Timesheet: () =>
				frappe.model.open_mapped_doc({
					method: "erpnext.projects.doctype.task.task.make_timesheet",
					frm: frm,
				}),
		};
	},

	refresh(frm) {
		// alert(frm.doc.revision_table.length);
		if (
			frm.doc.status == "Testing Open" ||
			frm.doc.status == "Ongoing Testing"
		)
			if (frm.doc.revision_table.length > 0) {
				frappe.confirm(
					'There is a revision in your task, if you set the status to <strong style="font-weight: bold;">' +
						frm.doc.status +
						"</strong>, the Revision Table will be deleted, are you sure you want to proceed?",
					() => {
						frm.clear_table("revision_table");
						frappe.msgprint({
							title: __("Notification"),
							indicator: "green",
							message: __(
								"Revision Table has been deleted successfully"
							),
						});
					},
					() => {
						frm.set_value("status", "Revision");
						cur_frm.save();
					}
				);

				frm.set_query("task", "depends_on", function () {
					let filters = {
						name: ["!=", frm.doc.name],
					};
					if (frm.doc.project) filters["project"] = frm.doc.project;
					return {
						filters: filters,
					};
				});
			}

		if (
			frm.doc.parent_cd_task != "" ||
			(frm.doc.parent_cd_task != null &&
				frm.doc.parent_cd_task != undefined)
		) {
			frm.set_df_property("exp_start_date", "read_only", 0);
			frm.set_df_property("exp_end_date", "read_only", 0);
		} else {
			frm.set_df_property("exp_start_date", "read_only", 1);
			frm.set_df_property("exp_end_date", "read_only", 1);
		}

		if (
			frm.doc.revision_start_date == "" ||
			(frm.doc.revision_end_date == "" && frm.doc.status === "Completed")
		) {
			frm.set_df_property("revision_start_date", "hidden", 1);
			frm.set_df_property("revision_end_date", "hidden", 1);
			frm.set_df_property("total_revision_hours", "hidden", 1);
		} else {
			frm.set_df_property("revision_start_date", "hidden", 0);
			frm.set_df_property("revision_end_date", "hidden", 0);
			frm.set_df_property("total_revision_hours", "hidden", 0);
		}

		// console.log(cur_frm.fields_dict);

		if (frm.doc.revision_table && frm.doc.revision_table.length > 0) {
			for (
				let index = 0;
				index < frm.doc.revision_table.length;
				index++
			) {
				const element = frm.doc.revision_table[index];
				if (element.revision_testing_start_date == null) {
					element.testing_type = "";
					element.testing_weight = "";
				}
			}
		}
	},

	onload: function (frm) {
		frm.set_query("parent_cd_task", function () {
			let filters = {
				is_group: 1,
				name: ["!=", frm.doc.name],
			};
			if (frm.doc.project) filters["project"] = frm.doc.project;
			return {
				filters: filters,
			};
		});

		cur_frm.cscript.department = function (doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			if (child.department != child.department_before) {
				child.task_type = "";
				refresh_field("task_type");
			}
		};

		frm.set_query("task_type", function () {
			let filters = {
				department: ["=", frm.doc.department],
			};
			//if (frm.doc.department != department) frm.doc.task_type = "";
			return {
				filters: filters,
			};
		});
	},

	is_group: function (frm) {
		frappe.call({
			method: "erpnext.projects.doctype.task.task.check_if_child_exists",
			args: {
				name: frm.doc.name,
			},
			callback: function (r) {
				if (r.message.length > 0) {
					let message = __(
						"Cannot convert Task to non-group because the following child Tasks exist: {0}.",
						[r.message.join(", ")]
					);
					frappe.msgprint(message);
					frm.reload_doc();
				}
			},
		});
	},

	validate: function (frm) {
		frm.doc.project &&
			frappe.model.remove_from_locals("CD Project", frm.doc.project);

		if (frm.doc.is_group == true) {
			frm.doc.task_type = null;
			frm.doc.task_weight = null;
		}

		if (frm.doc.testing_table && frm.doc.testing_table.length > 0) {
			for (let index = 0; index < frm.doc.testing_table.length; index++) {
				const element = frm.doc.testing_table[index];
				if (element.testing_completed == false) {
					element.testing_total_hours = null;
				}
			}
		}

		if (frm.doc.revision_table && frm.doc.revision_table.length > 0) {
			for (
				let index = 0;
				index < frm.doc.revision_table.length;
				index++
			) {
				const element = frm.doc.revision_table[index];
				if (element.revision_completed == false) {
					element.testing_revision_completed = false;
					element.revision_testing_start_date = null;
					element.revision_total_hours = null;
					element.testing_type = "";
					element.testing_weight = "";
				}
			}
		}
	},
});
