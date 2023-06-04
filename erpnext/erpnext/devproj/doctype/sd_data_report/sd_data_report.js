// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('SD Data Report', {
	onload: function (frm) {
		// Check if the document is newly created
		var childTable = frm.doc.task;
		var sum = 0;
		if (childTable && childTable.length > 0) {

			for (var i = 0; i < childTable.length; i++) {

				var fieldValue = childTable[i].task_weight;


				if (fieldValue && !isNaN(fieldValue)) {
					sum += parseFloat(fieldValue);
				}
			}
		}
		frm.set_value('total_weight', sum);

		frm.set_value('task_taken', childTable.length);
	}
});
