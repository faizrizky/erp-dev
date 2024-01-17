frappe.listview_settings["Support Ticket"] = {
	add_fields: ["status", "priority", "naming_series"],
	filters: [["status", "=", "Open"]],

	get_indicator: function (doc) {
		var colors = {
			Open: "blue",
			Replied: "cyan",
			Resolved: "purple",
			Closed: "green",
			"On Hold": "orange",
		};
		return [__(doc.status), colors[doc.status], "status,=," + doc.status];
	},
};
