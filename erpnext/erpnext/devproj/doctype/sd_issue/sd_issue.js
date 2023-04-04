// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('SD Issue', {
	// refresh: function(frm) {
	after_save(frm) {
		frm.set_df_property('task_issue', 'read_only', 1)
	}
	// }
});
