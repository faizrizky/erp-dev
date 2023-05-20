// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('SD Assets', {
	refresh: function (frm) {
		if (frm.doc.docstatus == 1) {
			if (in_list(["Submitted", "Partially Depreciated", "Fully Depreciated"], frm.doc.status)) {
				frm.add_custom_button(__("Transfer Asset"), function () {
					erpnext.asset.transfer_asset(frm);
				}, __("Manage"));

				frm.add_custom_button(__("Scrap Asset"), function () {
					erpnext.asset.scrap_asset(frm);
				}, __("Manage"));

				frm.add_custom_button(__("Sell Asset"), function () {
					frm.trigger("make_sales_invoice");
				}, __("Manage"));

			} else if (frm.doc.status == 'Scrapped') {
				frm.add_custom_button(__("Restore Asset"), function () {
					erpnext.asset.restore_asset(frm);
				}, __("Manage"));
			}

			if (frm.doc.maintenance_required && !frm.doc.maintenance_schedule) {
				frm.add_custom_button(__("Maintain Asset"), function () {
					frm.trigger("create_asset_maintenance");
				}, __("Manage"));
			}

			frm.add_custom_button(__("Repair Asset"), function () {
				frm.trigger("create_asset_repair");
			}, __("Manage"));

			frm.add_custom_button(__("Split Asset"), function () {
				frm.trigger("split_asset");
			}, __("Manage"));

			if (frm.doc.status != 'Fully Depreciated') {
				frm.add_custom_button(__("Adjust Asset Value"), function () {
					frm.trigger("create_asset_value_adjustment");
				}, __("Manage"));
			}

			if (!frm.doc.calculate_depreciation) {
				frm.add_custom_button(__("Create Depreciation Entry"), function () {
					frm.trigger("make_journal_entry");
				}, __("Manage"));
			}

			if (frm.doc.purchase_receipt || !frm.doc.is_existing_asset) {
				frm.add_custom_button(__("View General Ledger"), function () {
					frappe.route_options = {
						"voucher_no": frm.doc.name,
						"from_date": frm.doc.available_for_use_date,
						"to_date": frm.doc.available_for_use_date,
						"company": frm.doc.company
					};
					frappe.set_route("query-report", "General Ledger");
				}, __("Manage"));
			}

			if (frm.doc.depr_entry_posting_status === "Failed") {
				frm.trigger("set_depr_posting_failure_alert");
			}

			frm.trigger("setup_chart");
		}
	}
});
