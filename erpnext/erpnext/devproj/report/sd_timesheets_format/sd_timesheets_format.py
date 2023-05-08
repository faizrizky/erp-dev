# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.desk.reportview import build_match_conditions
from frappe.utils import getdate
from frappe.utils import nowdate
import datetime

def filter_date(filters=None):
	event = frappe.db.get_list('Event',
			filters={
				'name': filters.get("event_name")
			},
							fields=['starts_on', 'name', 'ends_on'],
							order_by='starts_on desc',
							# page_length=2,
							as_list=False
							)
	# print("Starts ON : ",event[0].ends_on)


	date_start = event[0].starts_on
	date_end = event[0].ends_on 

	return date_start, date_end

def execute(filters=None):

	if filters.get("event_name"):

		filter_date(filters)
		# date_str_start = date_start[0].strftime("%Y-%m-%d") # convert the first date object to a string
		# date_str_end = date_end[0].strftime("%Y-%m-%d") # convert the first date object to a string
		# print(date_str_start) 
		# print(date_str_end) 

		if not filters:
			filters = {}
		elif filters.get("event_name"):
			filters["from_time"] = "00:00:00"
			filters["to_time"] = "24:00:00"
			filters["from_date"] = filter_date(filters)[0]
			filters["to_date"] = filter_date(filters)[1]

		print(filters)
		# print(filters.get("from_date"))


		columns = get_column()
		conditions = get_conditions(filters)
		data = get_data(conditions, filters)

		# print(data)

		return columns, data


def get_column():
	return [
		_("Date") + "::120",
		_("Timesheets") + ":Link/SD Timesheets:120",
		_("Employee Name") + "::250",
		_("From Datetime") + "::170",
		_("To Datetime") + "::170",
		_("Total Hours") + "::120",
		# _("Activity Type") + "::120",
		_("Task") + ":Link/Task:150",
		_("Project") + ":Link/Project:170",
		# _("Status") + "::70",
		# _("Weight") + "::150",
	]


def get_data(conditions, filters):
	# GROUP BY `tabSD Timesheets`.name 
	time_sheet = frappe.db.sql(
		"""SELECT 
		`tabSD Timesheets`.start_date, 
		`tabSD Timesheets`.name, 
		`tabSD Timesheets`.employee_name,
		`tabTimesheet Detail`.from_time, 
		`tabTimesheet Detail`.to_time, 
		`tabTimesheet Detail`.hours_count,
		`tabTimesheet Detail`.task, 
		`tabTimesheet Detail`.project
		FROM 
		`tabTimesheet Detail`, 
		`tabSD Timesheets` 
		WHERE 
		`tabTimesheet Detail`.parent = `tabSD Timesheets`.name 
		AND %s 
		
		ORDER BY `tabSD Timesheets`.start_date""" % (conditions), filters, as_list=1)

	return time_sheet


def get_conditions(filters):
	conditions = "`tabSD Timesheets`.docstatus = 1"
	filter_date(filters)
	filter_dates = filter_date(filters) # get the list of dates from the filter
    # conditions += f" and `tabTimesheet Detail`.from_time >= '{filter_dates[0]}'"
	if filter_dates: # check if the list is non-empty
		conditions += " and `tabTimesheet Detail`.from_time >= timestamp('{0}', %(from_time)s)".format(filter_dates[0])
		conditions += " and `tabTimesheet Detail`.to_time <= timestamp('{0}',%(to_time)s)".format(filter_dates[1])

	match_conditions = build_match_conditions("Timesheet")
	if match_conditions:
		conditions += " and %s" % match_conditions

	return conditions
