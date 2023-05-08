// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["SD Timesheets Format"] = {
	"filters": [
		// {
		// 	"fieldname": "from_date",
		// 	"label": __("From Date"),
		// 	"fieldtype": "Date",
		// 	// "default": frappe.datetime.get_today()
		// },
		// {
		// 	"fieldname": "to_date",
		// 	"label": __("To Date"),
		// 	"fieldtype": "Date",
		// 	// "default": frappe.datetime.get_today()
		// },
		{
			fieldname: "event_name",
			label: __("Sprint"),
			fieldtype: "Link",
			options: "Event",
			// "default": 'SPRINT - 4',
			reqd: 0
		},
	]
};
