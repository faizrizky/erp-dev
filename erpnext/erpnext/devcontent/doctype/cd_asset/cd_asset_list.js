frappe.listview_settings["CD Asset"] = {
    get_indicator: function (doc) {
		var colors = {
			"Stored": "green",
			"Borrowed": "blue",
			"In Maintenance": "orange",
			"Missing": "red",
		}
        
		return [__(doc.status), colors[doc.status], "status,=," + doc.status];
	},
};
