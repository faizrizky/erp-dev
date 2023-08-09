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
			reqd: 0,
			custom_values_after: function (filter) {
				var project = filter["project_name"];
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
		{
			fieldname: "branch",
			label: __("Position"),
			fieldtype: "Link",
			options: "Branch",
			reqd: 0
		}
	]
};

