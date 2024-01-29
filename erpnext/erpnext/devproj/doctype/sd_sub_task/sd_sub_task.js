// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

document.validate_rename = function (value) {
	var regex = /-/g;

	if (this.frm.doc.status == "Completed") {
		frappe.throw({
			message: __(
				"Your Sub Task status is {0}. You can't rename a Task while status is {0}. Please move your task to another status, then try to rename it.",
				["<b>" + this.frm.doc.status + "</b>"]
			),
			title: __("Invalid Task Name"),
		});
	}

	if (
		value.title.match(regex) !== null &&
		value.title.match(regex).length >= 0
	) {
		frappe.throw({
			message: __(
				"{0} is using hyphen (-). You can't add hypen (-) on Sub Task.",
				["<b>" + value.title + "</b>"]
			),
			title: __("Invalid Task Name"),
		});
	}
};


frappe.ui.form.on('SD Sub Task', {

	project: function (frm) {
		var savedSelectedProject = frm.doc.__unsaved ? null : frm.doc.project;
		frm.set_query("project", function () {
			let filters = {
				_assign: ["like", "%" + frappe.session.user + "%"],
			};
			// console.log(savedSelectedProject, frm.doc.project)
			if (savedSelectedProject !== frm.doc.project) {
				frm.doc.task = null;
				frm.refresh_field('task');
			}
			return {
				filters: filters,
			};
		});
	},
	onload: function (frm) {

		frm.set_query("task", function () {
			let filters = {
				project: frm.doc.project,
				status: ["!=", "Cancelled"],
				_assign: ["like", "%" + frappe.session.user + "%"],
			};
			return {
				filters: filters,
			};
		});

	},
	department: function (frm) {
		frm.set_query("department", function () {
			if (frm.doc.department == "Document Engineer" || frm.doc.department == "Technical Architect Document Engineer") {
				console.log("EXECUTED")
				frm.doc.qa_weight = 0;
				frm.refresh_field('qa_weight');
			}
		});

	}
});
