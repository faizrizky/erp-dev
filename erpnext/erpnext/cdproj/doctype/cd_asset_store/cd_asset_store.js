// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('CD Asset Store', {
	refresh: function(frm) {
		frm.fields_dict.asset_name.get_query = function () {
			return {
				filters: {
					status: ['!=', "Fixed Asset"],
				},
			};
		};
	}
});
