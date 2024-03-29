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
	}
};

frappe.ui.form.on("Task", {
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
		if (frm.doc.qa_total_day == "") {
			frm.doc.qa_total_day = 0;
		}
		if (frm.doc.sub_task.length > 0 || frm.doc.status != "Working") {
			// console.log(frm.doc.sub_task.length)
			frm.set_df_property("individual_progress", "read_only", 1);
			frm.set_df_property("qa_progress", "read_only", 1);
		} else frm.set_df_property("individual_progress", "read_only", 0);
		frm.set_df_property("qa_progress", "read_only", 0);

		if (frm.doc.sub_task.length > 0 || frm.doc.status != "QA Testing") {
			// console.log(frm.doc.sub_task.length)
			frm.set_df_property("qa_progress", "read_only", 1);
		} else frm.set_df_property("qa_progress", "read_only", 0);
	},

	onload: function (frm) {
		frm.set_query("task", "depends_on", function () {
			let filters = {
				name: ["!=", frm.doc.name],
			};
			if (frm.doc.project) filters["project"] = frm.doc.project;
			return {
				filters: filters,
			};
		});

		frm.set_query("ongoing_sprint", function () {
			let filters = {
				status: ["=", "Open"],
			};

			return {
				filters: filters,
			};
		});

		frm.set_query("parent_task", function () {
			let filters = {
				is_group: 1,
				name: ["!=", frm.doc.name],
			};
			if (frm.doc.project) filters["project"] = frm.doc.project;
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
			frappe.model.remove_from_locals("Project", frm.doc.project);
	},
});
