frappe.listview_settings["CD Asset"] = {
    get_indicator: function (doc) {
		var colors = {
			"Stored": "green",
			"Borrowed": "blue",
			"Fixed Asset": "darkgrey",
			"Hardware": "red",
		}

		return [__(doc.status), colors[doc.status], "status,=," + doc.status];	
	},
};
