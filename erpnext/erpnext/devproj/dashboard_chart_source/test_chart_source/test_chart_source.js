// Copyright (c) 2019, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.provide('frappe.dashboards.chart_sources')

frappe.dashboards.chart_sources['Test Chart Source'] = {
    method: "erpnext.devproj.dashboard_chart_source.test_chart_source.test_chart_source.get",
    filters: [
        {
            fieldname: "name",
            label: __("Project"),
            fieldtype: "Link",
            options: "Project",
            default: frappe.defaults.get_user_default("Project"),
            reqd: 0
        }
    ]
}