# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from frappe import _

class SDSubTask(Document):
    def validate(self):
        self.validate_name()
        self.validate_weight()
        
    def validate_name(self):
        if '-' in self.subject:
            frappe.throw(("{0} is using hyphen (-). You can't add hypen (-) on Sub Task.").format(frappe.bold(self.subject)),title=_("Invalid Sub Task Name"))
    
    def validate_weight(self):
        if self.weight != None:
            if self.weight > 4 or self.weight < 1:
                frappe.throw(_("Please set {0} value between {1}")
								.format(frappe.bold("Weight"), frappe.bold("1 to 4")),title=_("Invalid Weight"))
        else:
            frappe.throw(_("{0} cannot be {1}.")
											.format(frappe.bold("Weight"), frappe.bold("empty")),title=_("Invalid QA Weight"))
        
        if self.qa_weight != None:
            if self.qa_weight > 4 or self.qa_weight < 1 and self.department != "Document Engineer" or self.department != "Technical Architect Document Engineer":
                frappe.throw(_("Please set {0} value between {1}")
											.format(frappe.bold("Sub Task QA Weight"), frappe.bold("1 to 4")),title=_("Invalid QA Weight"))
        else:
            if self.department == "Document Engineer" or self.department == "Technical Architect Document Engineer":
                self.qa_weight = "0"
            
            else:
                frappe.throw(_("{0} cannot be {1}.")
											.format(frappe.bold("QA Weight"), frappe.bold("empty")),title=_("Invalid QA Weight"))
			
  	

