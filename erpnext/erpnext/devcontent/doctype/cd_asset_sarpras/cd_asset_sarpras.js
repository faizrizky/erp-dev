// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('CD Asset Sarpras', {
	// refresh: function(frm){	
	// }
	room: function(frm){
		frm.fields_dict["assets"].grid.get_field("asset_name").get_query =
			function () {
				return {
					filters: {
						sarpras_type: ["=", "General"],
						room: ["=", frm.fields_dict["room"].last_value],
					},
				};
			};
	}
});