// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('CD Assets Movement', {
	purpose: function(frm){
		if (frm.fields_dict["purpose"].last_value == "Borrow") {
			// This Function Get List Grid With Filter.
			// (borrow_asset_list) is fieldname in doctype cd asset movement with type table from child table cd asset borrow.
			// (asset_name) is field with type link from doctype cd asset borrow in from parent cd asset movement
			frm.fields_dict["borrow_asset_list"].grid.get_field("asset_name").get_query =
			function () {
				return {
					filters: { status: ["!=", "Fixed Asset"], employee: frm.fields_dict["borrow_asset_list"].grid.data[0].to_employee },
				};
			};	
		}
		else if(frm.fields_dict["purpose"].last_value == "Transfer"){
			// This Function Get List Grid With Filter.
			// (transfer_asset_list) is fieldname in doctype cd asset movement with type table from child table cd asset transfer.
			// (asset_name_transfer) is field with type link from doctype cd asset transfer in from parent cd asset movement
			frm.fields_dict["transfer_asset_list"].grid.get_field("asset_transfer").get_query =
			function () {
				return { filters: { status: ["!=", "Fixed Asset"], }, };
			};
		}
	},
	refresh: function(frm){
		// This Function Get Method From Controller Python In CD Asset Movement With Withlist Frappe
		frm.call('get_linked_doc').callback(r => { console.log(r) })
	}
});