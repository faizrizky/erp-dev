// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('SD Issue', {
	// refresh: function(frm) {
	// after_save(frm) {
	// 	frm.set_df_property('task_issue', 'read_only', 1)
	// }
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
