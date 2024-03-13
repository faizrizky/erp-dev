// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

function checkSubTaskLength(doc) {
	var subTasksFilter = []; // Declare subTasksFilter variable here

	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Task",
			filters: { subject: doc },
			fields: ["sub_task.sub_task"]
		},
		async: false,
		callback: function (response) {
			if (response && response.message) {
				var subTasks = response.message.map(entry => entry.sub_task ? entry.sub_task[0].sub_task : null);
				subTasksFilter = subTasks.filter(subTask => {
					if (subTask !== null) {
						return true;
					}
					return false;
				});
			}
		},
	});
	return subTasksFilter;
}

frappe.ui.form.on("SD Timesheets", {
	// refresh: function(frm) {

	// }

	setup: function (frm) {
		console.log("Executed in setuo")
		frappe.require("/assets/erpnext/js/projects/timer.js");

		frm.fields_dict.employee.get_query = function () {
			return {
				filters: {
					status: "Active",
				},
			};
		};

		frm.set_query("ongoing_sprint", function () {
			let filters = {
				status: ["=", "Open"],
			};

			return {
				filters: filters,
			};
		});

		frm.fields_dict["time_logs"].grid.get_field("task").get_query =
			function (frm, cdt, cdn) {
				var child = locals[cdt][cdn];
				return {
					filters: {
						project: child.project,
						ongoing_sprint: ["!=", ""],
						status: ["not in", ["Cancelled", "Completed"]],
						_assign: ["like", "%" + frappe.session.user + "%"],
					},
				};
			};

		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Employee",
				filters: { user_id: frappe.session.user },
				fieldname: ["branch"],
			},
			callback: function (response) {
				if (response && response.message) {
					var user_branch = response.message.branch;

					frm.fields_dict['time_logs'].grid.get_field('sub_task').get_query = function (doc, cdt, cdn) {
						var child = locals[cdt][cdn];
						var filters = {
							status: ["!=", "Cancelled"],
							task: child.task,
							_assign: ["like", "%" + frappe.session.user + "%"],
						};

						// Check if user_branch is not "Quality Assurance"
						if (user_branch !== "Quality Assurance") {
							filters.department = ["like", "%" + user_branch + "%"];
						}

						return {
							filters: filters
						};
					};
				}
			}
		});

		frm.fields_dict["time_logs"].grid.get_field("project").get_query =
			function () {
				return {
					filters: {
						company: frm.doc.company,
						status: ["=", ["Open"]],
						_assign: ["like", "%" + frappe.session.user + "%"],
					},
				};
			};
	},

	before_load: function (frm) {

		if ((frm.doc.end_date != null) && (frm.doc.docstatus == 0)) {
			frm.doc.end_date = frappe.datetime.get_today()
		}

		console.log("Executed before load")
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Employee",
				filters: { user_id: frappe.session.user },
				fieldname: ["employee_name"],
			},
			callback: function (response) {

				if (response && response.message) {
					var user_employee_name = response.message.employee_name;
					if (user_employee_name === frm.doc.employee_name && frm.doc.start_date == frappe.datetime.get_today() && frm.doc.docstatus == 1) {
						frappe.call({
							method: "frappe.client.get_list",
							args: {
								doctype: "SD Timesheets",
								filters: {
									start_date: frappe.datetime.get_today(),
									employee_name: user_employee_name,
									docstatus: 1
								},

							},
							callback: function (response) {
								if (response && response.message) {
									console.log("Number of SD Timesheets Today:", response.message.length);
									console.log("Date:", frappe.datetime.get_today());
									if (response.message.length >= 1) {
										frappe.msgprint({
											title: __("Multiple Timesheets Detected"),
											indicator: 'red',
											message: __("You cannot create multiple Timesheets in a day. Redirecting to SD Timesheets page."),
										});

										frappe.set_route("List", "SD Timesheets");
									}
								}
							}
						});
					}

				}
			}
		});


	},

	onload: function (frm) {
		console.log("Executed on onload")
		if (frm.doc.__islocal && frm.doc.time_logs) {
			calculate_time_and_amount(frm);
		}

		if (frm.is_new() && !frm.doc.employee) {
			set_employee_and_company(frm);
		}

		if ((frm.doc.end_date != null) && (frm.doc.docstatus == 0)) {
			frm.doc.end_date = frappe.datetime.get_today()
		}
	},

	// after_save: function (frm) {

	// },

	on_submit: function (frm) {
		let end_date_today = frappe.datetime.get_today();

		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "SD Timesheets",
				filters: {
					title: frm.doc.employee_info,
					end_date: [">=", end_date_today],
					docstatus: 1,
				},
				limit: 1,
			},
			callback: function (response) {
				// Check if response.message is valid
				if (
					response &&
					response.message &&
					response.message.length > 0
				) {
					// Handle the response
					if (frm.doc.docstatus == 1) {
						frappe.show_alert(
							{
								message: __(
									'Your working hours will be stored to <strong style="font-weight: bold;">' +
									"Timesheet Table" +
									"</strong>, in every Task you choose."
								),
								indicator: "green",
							},
							7
						);
					}
					// } else {
					// 	frappe.confirm(
					// 		'This data will be stored to <strong style="font-weight: bold;">' +
					// 			"Timesheet Table" +
					// 			"</strong>, in every Task you choose, are you sure you want to proceed?",
					// 		() => {
					// 			// frm.clear_table("revision_table");
					// 			cur_frm.save("Cancel");
					// 			frappe.msgprint({
					// 				title: __("Notification"),
					// 				indicator: "green",
					// 				message: __(
					// 					"Revision Table has been deleted successfully"
					// 				),
					// 			});
					// 		},
					// 		() => {
					// 			// frm.set_value("status", "Revision");
					// 			// cur_frm.save();
					// 		}
					// 	);
				}
			},
			error: function (xhr, textStatus, error) {
				// Handle the error
				console.error(xhr.responseText);
			},
		});
	},

	refresh: function (frm, cdt, cdn) {
		console.log("Executed on refresh")

		if (frm.doc.docstatus == 1) {
			if (
				frm.doc.per_billed < 100 &&
				frm.doc.total_billable_hours &&
				frm.doc.total_billable_hours > frm.doc.total_billed_hours
			) {
				frm.add_custom_button(__("Create Sales Invoice"), function () {
					frm.trigger("make_invoice");
				});
			}
		}

		var timeLogs = frm.doc.time_logs;
		var subTaskField = frm.fields_dict['time_logs'];
		// console.log("Total Timesheet : ", timeLogs.length)

		if (timeLogs && timeLogs.length > 0) {
			var lastTask = timeLogs[timeLogs.length - 1].task;
			if (lastTask !== undefined) {
				frappe.call({
					method: 'frappe.client.get',
					args: {
						doctype: 'Task',
						name: lastTask
					},
					callback: function (response) {
						var doc = response.message;
						/*
						console.log("subTaskField : ", subTaskField.doc.time_logs[timeLogs.length - 1].sub_task)
						for (let index = 0; index < doc.sub_task.length; index++) {
							const element = doc.sub_task[index].sub_task;
							console.log('Task Document Name:', element);
						}
						
						// console.log("Total Sub Task : ", response.message.sub_task.length)
						*/

						if (response.message && doc.sub_task.length > 0) {
							subTaskField.grid.toggle_display('sub_task', true);
							if (timeLogs[timeLogs.length - 1].sub_task == undefined) {
								frappe.msgprint(__("Sub Task cannot be null. Please select a sub task."));
								throw __("Sub Task cannot be null.");
							}
							// console.log("TASK : ", timeLogs[timeLogs.length - 1].task)
						}
						else {
							subTaskField.grid.toggle_display('sub_task', false);
							// console.log("TASK MASUK ELSE : ", timeLogs[timeLogs.length - 1].task)
						}
					}
				});
			}
			else {
				console.log("Undifiened")
			}
		}

		if (frm.doc.docstatus < 1) {
			let button = "Start Timer";
			$.each(frm.doc.time_logs || [], function (i, row) {
				if (
					row.from_time <= frappe.datetime.now_datetime() &&
					!row.completed
				) {
					button = "Resume Timer";
				}
			});

			frm.add_custom_button(__(button), function () {
				var flag = true;
				$.each(frm.doc.time_logs || [], function (i, row) {
					// Fetch the row for which from_time is not present
					if (flag && row.activity_type && !row.from_time) {
						erpnext.timesheet.timer(frm, row);
						row.from_time = frappe.datetime.now_datetime();
						let d = moment(row.from_time);
						if (row.expected_hours) {
							d.add(row.expected_hours, "minute");
							row.to_time = d.format(frappe.defaultDatetimeFormat);
						}
						frm.refresh_fields("time_logs");
						frm.save();
						flag = false;
					}
					// Fetch the row for timer where activity is not completed and from_time is before now_time
					if (
						flag &&
						row.from_time <= frappe.datetime.now_datetime() &&
						!row.completed
					) {
						let timestamp = moment(
							frappe.datetime.now_datetime()
						).diff(moment(row.from_time), "seconds");
						erpnext.timesheet.timer(frm, row, timestamp);
						flag = false;
					}
				});
				// If no activities found to start a timer, create new
				if (flag) {
					erpnext.timesheet.timer(frm);
				}
			}).addClass("btn-primary");
		}
		if (frm.doc.per_billed > 0) {
			frm.fields_dict["time_logs"].grid.toggle_enable(
				"billing_hours",
				false
			);
			frm.fields_dict["time_logs"].grid.toggle_enable(
				"is_billable",
				false
			);
		}

		let filters = {
			status: "Open",
		};

		if (frm.doc.customer) {
			filters["customer"] = frm.doc.customer;
		}

		frm.set_query("parent_project", function (doc) {
			return {
				filters: filters,
			};
		});

		frm.trigger("setup_filters");
		frm.trigger("set_dynamic_field_label");
	},

	customer: function (frm) {
		frm.set_query("project", "time_logs", function (doc) {
			return {
				filters: {
					customer: doc.customer,
				},
			};
		});
		frm.refresh();
	},

	currency: function (frm) {
		let base_currency = frappe.defaults.get_global_default("currency");
		if (frm.doc.currency && base_currency != frm.doc.currency) {
			frappe.call({
				method: "erpnext.setup.utils.get_exchange_rate",
				args: {
					from_currency: frm.doc.currency,
					to_currency: base_currency,
				},
				callback: function (r) {
					if (r.message) {
						frm.set_value("exchange_rate", flt(r.message));
						frm.set_df_property(
							"exchange_rate",
							"description",
							"1 " + frm.doc.currency + " = [?] " + base_currency
						);
					}
				},
			});
		}
		frm.trigger("set_dynamic_field_label");
	},

	exchange_rate: function (frm) {
		$.each(frm.doc.time_logs, function (i, d) {
			calculate_billing_costing_amount(frm, d.doctype, d.name);
		});
		calculate_time_and_amount(frm);
	},

	set_dynamic_field_label: function (frm) {
		let base_currency = frappe.defaults.get_global_default("currency");
		frm.set_currency_labels(
			[
				"base_total_costing_amount",
				"base_total_billable_amount",
				"base_total_billed_amount",
			],
			base_currency
		);
		frm.set_currency_labels(
			[
				"total_costing_amount",
				"total_billable_amount",
				"total_billed_amount",
			],
			frm.doc.currency
		);

		frm.toggle_display(
			[
				"base_total_costing_amount",
				"base_total_billable_amount",
				"base_total_billed_amount",
			],
			frm.doc.currency != base_currency
		);

		if (frm.doc.time_logs.length > 0) {
			frm.set_currency_labels(
				[
					"base_billing_rate",
					"base_billing_amount",
					"base_costing_rate",
					"base_costing_amount",
				],
				base_currency,
				"time_logs"
			);
			frm.set_currency_labels(
				[
					"billing_rate",
					"billing_amount",
					"costing_rate",
					"costing_amount",
				],
				frm.doc.currency,
				"time_logs"
			);

			let time_logs_grid = frm.fields_dict.time_logs.grid;
			$.each(
				[
					"base_billing_rate",
					"base_billing_amount",
					"base_costing_rate",
					"base_costing_amount",
				],
				function (i, d) {
					if (frappe.meta.get_docfield(time_logs_grid.doctype, d))
						time_logs_grid.set_column_disp(
							d,
							frm.doc.currency != base_currency
						);
				}
			);
		}
		frm.refresh_fields();
	},

	make_invoice: function (frm) {
		let fields = [
			{
				fieldtype: "Link",
				label: __("Item Code"),
				fieldname: "item_code",
				options: "Item",
			},
		];

		if (!frm.doc.customer) {
			fields.push({
				fieldtype: "Link",
				label: __("Customer"),
				fieldname: "customer",
				options: "Customer",
				default: frm.doc.customer,
			});
		}

		let dialog = new frappe.ui.Dialog({
			title: __("Create Sales Invoice"),
			fields: fields,
		});

		dialog.set_primary_action(__("Create Sales Invoice"), () => {
			var args = dialog.get_values();
			if (!args) return;
			dialog.hide();
			return frappe.call({
				type: "GET",
				method: "erpnext.projects.doctype.timesheet.timesheet.make_sales_invoice",
				args: {
					source_name: frm.doc.name,
					item_code: args.item_code,
					customer: frm.doc.customer || args.customer,
					currency: frm.doc.currency,
				},
				freeze: true,
				callback: function (r) {
					if (!r.exc) {
						frappe.model.sync(r.message);
						frappe.set_route(
							"Form",
							r.message.doctype,
							r.message.name
						);
					}
				},
			});
		});
		dialog.show();
	},

	parent_project: function (frm) {
		set_project_in_timelog(frm);
	},
});

frappe.ui.form.on("Timesheet Detail", {
	// employee_name: function (frm, cdt, cdn) {
	// 	console.log("Script executed");

	// 	var child = locals[cdt][cdn];
	// 	var employeeID = child.employee_name; // replace with the actual fieldname

	// 	console.log("Employee ID:", employeeID);

	// 	frappe.call({
	// 		method: "frappe.client.get",
	// 		args: {
	// 			doctype: "Employee",
	// 			name: employeeID,
	// 			filters: {}, // You can add filters if needed
	// 		},
	// 		callback: function (response) {
	// 			console.log("Server response:", response);

	// 			var employee = response.message;

	// 			// Assuming you want to set the employee name in your child record
	// 			frappe.model.set_value(
	// 				cdt,
	// 				cdn,
	// 				"employee_name",
	// 				employee.employee_name
	// 			);
	// 		},
	// 	});
	// },

	time_logs_remove: function (frm) {
		calculate_time_and_amount(frm);
	},

	task: (frm, cdt, cdn) => {
		console.log("Script executed");
		let row = frm.selected_doc;

		frappe.model.set_value(cdt, cdn, "sub_task", null);
		console.log(checkSubTaskLength(row.task))
		if (checkSubTaskLength(row.task).length >= 1) {
			frm.cur_grid.grid.toggle_display("sub_task", true);
			// frm.cur_grid.grid.toggle_reqd("sub_task", true);

		} else {
			frm.cur_grid.grid.toggle_display("sub_task", false);
			// frm.cur_grid.grid.toggle_reqd("sub_task", false);
			frappe.model.set_value(cdt, cdn, "sub_task", null);
		}

		if (row.task) {
			frappe.db.get_value("Task", row.task, "project", (r) => {
				frappe.model.set_value(cdt, cdn, "project", r.project);
			});
		}
	},


	from_time: function (frm, cdt, cdn) {
		calculate_end_time(frm, cdt, cdn);
	},

	to_time: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];

		if (frm._setting_hours) return;

		var hours =
			moment(child.to_time).diff(moment(child.from_time), "seconds") /
			3600;
		var hrs =
			moment(child.to_time).diff(moment(child.from_time), "seconds") /
			3600;
		frappe.model.set_value(cdt, cdn, "hours", hours);
		frappe.model.set_value(cdt, cdn, "hrs", hrs);
		console.log(frappe.model.set_value(cdt, cdn, "hrs", hrs));
	},

	time_logs_add: function (frm, cdt, cdn) {
		if (frm.doc.parent_project) {
			frappe.model.set_value(cdt, cdn, "project", frm.doc.parent_project);
		}
	},

	hours: function (frm, cdt, cdn) {
		calculate_end_time(frm, cdt, cdn);
		calculate_billing_costing_amount(frm, cdt, cdn);
		calculate_time_and_amount(frm);
	},

	billing_hours: function (frm, cdt, cdn) {
		calculate_billing_costing_amount(frm, cdt, cdn);
		calculate_time_and_amount(frm);
	},

	billing_rate: function (frm, cdt, cdn) {
		calculate_billing_costing_amount(frm, cdt, cdn);
		calculate_time_and_amount(frm);
	},

	costing_rate: function (frm, cdt, cdn) {
		calculate_billing_costing_amount(frm, cdt, cdn);
		calculate_time_and_amount(frm);
	},

	is_billable: function (frm, cdt, cdn) {
		update_billing_hours(frm, cdt, cdn);
		update_time_rates(frm, cdt, cdn);
		calculate_billing_costing_amount(frm, cdt, cdn);
		calculate_time_and_amount(frm);
	},

	activity_type: function (frm, cdt, cdn) {
		if (!frappe.get_doc(cdt, cdn).activity_type) return;

		frappe.call({
			method: "erpnext.projects.doctype.timesheet.timesheet.get_activity_cost",
			args: {
				employee: frm.doc.employee,
				activity_type: frm.selected_doc.activity_type,
				currency: frm.doc.currency,
			},
			callback: function (r) {
				if (r.message) {
					frappe.model.set_value(
						cdt,
						cdn,
						"billing_rate",
						r.message["billing_rate"]
					);
					frappe.model.set_value(
						cdt,
						cdn,
						"costing_rate",
						r.message["costing_rate"]
					);
					calculate_billing_costing_amount(frm, cdt, cdn);
				}
			},
		});
	},
});

var calculate_end_time = function (frm, cdt, cdn) {
	let child = locals[cdt][cdn];

	if (!child.from_time) {
		// if from_time value is not available then set the current datetime
		frappe.model.set_value(
			cdt,
			cdn,
			"from_time",
			frappe.datetime.get_datetime_as_string()
		);
	}

	let d = moment(child.from_time);
	console.log(child)
	if (child.hours) {
		console.log(child.hours)
		d.add(child.hours, "hours");
		frm._setting_hours = true;
		frappe.model
			.set_value(
				cdt,
				cdn,
				"to_time",
				d.format(frappe.defaultDatetimeFormat)
			)
			.then(() => {
				frm._setting_hours = false;
			});
	}
};

var update_billing_hours = function (frm, cdt, cdn) {
	let child = frappe.get_doc(cdt, cdn);
	if (!child.is_billable) {
		frappe.model.set_value(cdt, cdn, "billing_hours", 0.0);
	} else {
		// bill all hours by default
		frappe.model.set_value(cdt, cdn, "billing_hours", child.hours);
	}
};

var update_time_rates = function (frm, cdt, cdn) {
	let child = frappe.get_doc(cdt, cdn);
	if (!child.is_billable) {
		frappe.model.set_value(cdt, cdn, "billing_rate", 0.0);
	}
};

var calculate_billing_costing_amount = function (frm, cdt, cdn) {
	let row = frappe.get_doc(cdt, cdn);
	let billing_amount = 0.0;
	let base_billing_amount = 0.0;
	let exchange_rate = flt(frm.doc.exchange_rate);
	frappe.model.set_value(
		cdt,
		cdn,
		"base_billing_rate",
		flt(row.billing_rate) * exchange_rate
	);
	frappe.model.set_value(
		cdt,
		cdn,
		"base_costing_rate",
		flt(row.costing_rate) * exchange_rate
	);
	if (row.billing_hours && row.is_billable) {
		base_billing_amount =
			flt(row.billing_hours) * flt(row.base_billing_rate);
		billing_amount = flt(row.billing_hours) * flt(row.billing_rate);
	}

	frappe.model.set_value(
		cdt,
		cdn,
		"base_billing_amount",
		base_billing_amount
	);
	frappe.model.set_value(
		cdt,
		cdn,
		"base_costing_amount",
		flt(row.base_costing_rate) * flt(row.hours)
	);
	frappe.model.set_value(cdt, cdn, "billing_amount", billing_amount);
	frappe.model.set_value(
		cdt,
		cdn,
		"costing_amount",
		flt(row.costing_rate) * flt(row.hours)
	);
};

var calculate_time_and_amount = function (frm) {
	let tl = frm.doc.time_logs || [];
	let total_working_hr = 0;
	let total_billing_hr = 0;
	let total_billable_amount = 0;
	let total_costing_amount = 0;
	for (var i = 0; i < tl.length; i++) {
		if (tl[i].hours) {
			total_working_hr += tl[i].hours;
			total_working_hr = moment
				.utc(currentIncrement * 1000)
				.format("HH:mm:ss");
			total_billable_amount += tl[i].billing_amount;
			total_costing_amount += tl[i].costing_amount;

			if (tl[i].is_billable) {
				total_billing_hr += tl[i].billing_hours;
			}
		}
	}

	frm.set_value("total_billable_hours", total_billing_hr);
	frm.set_value("total_hours", total_working_hr);
	frm.set_value("total_billable_amount", total_billable_amount);
	frm.set_value("total_costing_amount", total_costing_amount);
};

// set employee (and company) to the one that's currently logged in
const set_employee_and_company = function (frm) {
	const options = { user_id: frappe.session.user };
	const fields = ["name", "company"];
	frappe.db.get_value("Employee", options, fields).then(({ message }) => {
		if (message) {
			// there is an employee with the currently logged in user_id
			frm.set_value("employee", message.name);
			frm.set_value("company", message.company);
		}
	});
};

function set_project_in_timelog(frm) {
	if (frm.doc.parent_project) {
		$.each(frm.doc.time_logs || [], function (i, item) {
			frappe.model.set_value(
				item.doctype,
				item.name,
				"project",
				frm.doc.parent_project
			);
		});
	}
}
