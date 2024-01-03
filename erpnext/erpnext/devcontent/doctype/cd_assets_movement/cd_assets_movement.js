// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('CD Assets Movement', {
	refresh: function(frm){
		// $('*[data-fieldname="borrow_asset_list"]').find('.grid-remove-rows').hide();
		frm.call('get_linked_doc').callback(r => { console.log(r) })
	}
});

// frappe.ui.form.on('CD Asset Borrow', {
// 	refresh(frm) {
// 		// your code here
// 	},
	
//     form_render(frm, cdt, cdn){
//         frm.fields_dict.borrow_asset_list.grid.wrapper.find('.grid-delete-row').hide();
//     }
// });