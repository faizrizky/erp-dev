// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('SD Asset Movement Item', {
	refresh(frm) {
		frm.set_df_property('from_employee', 'in_list_view', 1)

	}
});
