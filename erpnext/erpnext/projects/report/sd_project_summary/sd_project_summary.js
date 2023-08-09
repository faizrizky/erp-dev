// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["SD Project Summary"] = {
	"filters": [
		{
			fieldname: "name",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
			default: frappe.defaults.get_user_default("Project"),
			reqd: 0,
			custom_values_after: function (filter) {
				var project = filter["name"];
				var expected_end_date = "";
				var actual_end_date = "";
				var concatenated_str = "";

				if (project) {
					frappe.call({
						async: false,
						freeze: true,
						method: "frappe.client.get_value",
						args: {
							doctype: "Project",
							filters: { name: project },
							fieldname: ["expected_end_date", "actual_end_date"]
						},
						callback: function (response) {
							if (response.message) {
								expected_end_date = response.message.expected_end_date;
								actual_end_date = response.message.actual_end_date;

								if (expected_end_date) {
									concatenated_str += "<br><h6 class='text-secondary'>End Date: " + expected_end_date + "</h6>";
								}

								if (actual_end_date) {
									concatenated_str += "<h6 class='text-secondary'>Actual End Date: " + actual_end_date + "</h6>";
								}
							}
						}
					});
				}
				return concatenated_str;
			},
		},
		// {
		// 	"fieldname": "is_active",
		// 	"label": __("Is Active"),
		// 	"fieldtype": "Select",
		// 	"options": "\nYes\nNo",
		// 	"default": "Yes",
		// },
		// {
		// 	"fieldname": "status",
		// 	"label": __("Status"),
		// 	"fieldtype": "Select",
		// 	"options": "\nOpen\nCompleted\nCancelled",
		// 	"default": "Open"
		// },
		// {
		// 	"fieldname": "project_type",
		// 	"label": __("Project Type"),
		// 	"fieldtype": "Link",
		// 	"options": "Project Type"
		// },
		// {
		// 	"fieldname": "priority",
		// 	"label": __("Priority"),
		// 	"fieldtype": "Select",
		// 	"options": "\nLow\nMedium\nHigh"
		// }
	]
};
