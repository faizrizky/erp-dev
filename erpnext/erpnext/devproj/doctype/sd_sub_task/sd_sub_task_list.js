frappe.listview_settings["SD Sub Task"] = {
    add_fields: ["status", "department"],

    get_indicator: function (doc) {
        var colors = {
            "Open": "blue",
            "Working": "cyan",
            "Completed": "green",
            "Cancelled": "gray",
            "On Hold": "yellow",

        };
        return [__(doc.status), colors[doc.status], "status,=," + doc.status];

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
