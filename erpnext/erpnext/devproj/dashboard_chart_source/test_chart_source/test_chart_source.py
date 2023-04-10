# Copyright (c) 2019, Frappe Technologies and Contributors
# License: MIT. See LICENSE
from frappe.tests.utils import FrappeTestCase
import frappe
from frappe import _
from frappe.utils.dashboard import cache_source

@frappe.whitelist()
@cache_source
def get(
	chart_name = None,
	chart=None,
	no_cache=None,
	filters=None,
	from_date=None,
	to_date=None,
	timespan=None,
	time_interval=None,
	heatmap_year=None,
):
	labels, datapoints = [], []
	filters = frappe.parse_json(filters)

	task_filters = [["status","=","Open"]]

	tasks = frappe.get_list("Project", fields= ["name", "percent_complete"], filters=filters, order_by = "name")

	if not tasks:
		return []

	for task in tasks:
		labels.append(_(task.get("name")))
		datapoints.append(task.get("percent_complete"))

	return {
		"labels" : labels,
		"datasets" :[{"name": "In Percent (%)", "values": datapoints}],
		"type" :"bar",
		# "colors" : ["#f50000", "#f50000"]
	}