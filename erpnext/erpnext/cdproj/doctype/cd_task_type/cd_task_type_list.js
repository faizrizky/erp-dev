frappe.listview_settings["CD Task Type"] = {
	add_fields: ["weight", "department"],

	//filters: [["department", "=", "3D Artist"]],

	get_indicator: function (doc) {
		var colors = {
			"3D Artist": "blue",
			"2D Artist": "cyan",
			"Concept Artist": "green",
			"Video Editor": "pink",
		};
		return [
			__(doc.department),
			colors[doc.department],
			"department,=," + doc.department,
		];
	},
	// gantt_custom_popup_html: function (ganttobj, task) {
	// 	var html = `<h5><a style="text-decoration:underline"\
	// 		href="/app/task/${ganttobj.id}""> ${ganttobj.name} </a></h5>`;

	// 	if (task.project) html += `<p>Project: ${task.project}</p>`;
	// 	html += `<p>Progress: ${ganttobj.progress}</p>`;

	// 	if (task._assign_list) {
	// 		html += task._assign_list.reduce(
	// 			(html, user) => html + frappe.avatar(user),
	// 			""
	// 		);
	// 	}

	// 	return html;
	// },
};
