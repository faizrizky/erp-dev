import frappe

@frappe.whitelist()
def get_project() :
    return frappe.db.get_list('Project', pluck='name')
