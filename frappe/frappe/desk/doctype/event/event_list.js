frappe.listview_settings["Event"] = {
	add_fields: ["starts_on", "ends_on"],
	onload: function () {
		frappe.route_options = {
			status: "Open",
		};
	},

	get_indicator: function (doc) {
		var colors = {
			"Open": "blue",
			"Soon": "yellow",
			"Completed": "green",
			"Closed": "pink",
		}
		return [__(doc.status), colors[doc.status], "status,=," + doc.status];
	},
};
