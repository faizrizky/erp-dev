// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employee Report Project"] = {
	"filters": [
		{
			fieldname: "project_name",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
			default: frappe.defaults.get_user_default("Project"),
			reqd: 0
		},
		{
			fieldname: "team",
			label: __("Position"),
			fieldtype: "Link",
			options: "Branch",
			// default: frappe.defaults.get_user_default("Project"),
			reqd: 0
		},
	]
};
