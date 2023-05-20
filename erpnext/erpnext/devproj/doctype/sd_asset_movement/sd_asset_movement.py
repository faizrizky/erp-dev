# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe import _
from frappe.model.document import Document

class SDAssetMovement(Document):
	def validate(self):
		self.validate_asset()
		# self.validate_location()
		self.validate_employee()

	def validate_asset(self):
		has_missing = []
		for d in self.assets:
			status = frappe.db.get_value("SD Asset", d.asset, ["status"])
			has_missing.append(d.asset)
		if self.purpose == "Transfer" and status in ("Missing", "In Maintenance"):
			frappe.throw(_("{0} is {1}. {2} asset cannot be transferred").format(frappe.bold((" , ").join(has_missing)),frappe.bold(status),frappe.bold(status)))

			# if company != self.company:
			# 	frappe.throw(_("Asset {0} does not belong to company {1}").format(d.asset, self.company))

			# if not (d.source_location or d.target_location or d.from_employee or d.to_employee):
			# 	frappe.throw(_("Either location or employee must be required"))


	def validate_location(self):
		for d in self.assets:
			if self.purpose in ["Transfer", "Issue"]:
				if not d.source_location:
					d.source_location = frappe.db.get_value("Asset", d.asset, "location")

				if not d.source_location:
					frappe.throw(_("Source Location is required for the Asset {0}").format(d.asset))

				if d.source_location:
					current_location = frappe.db.get_value("Asset", d.asset, "location")

					if current_location != d.source_location:
						frappe.throw(
							_("Asset {0} does not belongs to the location {1}").format(d.asset, d.source_location)
						)

			if self.purpose == "Issue":
				if d.target_location:
					frappe.throw(
						_(
							"Issuing cannot be done to a location. Please enter employee who has issued Asset {0}"
						).format(d.asset),
						title=_("Incorrect Movement Purpose"),
					)
				if not d.to_employee:
					frappe.throw(_("Employee is required while issuing Asset {0}").format(d.asset))

			if self.purpose == "Transfer":
				if d.to_employee:
					frappe.throw(
						_(
							"Transferring cannot be done to an Employee. Please enter location where Asset {0} has to be transferred"
						).format(d.asset),
						title=_("Incorrect Movement Purpose"),
					)
				if not d.target_location:
					frappe.throw(_("Target Location is required while transferring Asset {0}").format(d.asset))
				if d.source_location == d.target_location:
					frappe.throw(_("Source and Target Location cannot be same"))

			if self.purpose == "Receipt":
				# only when asset is bought and first entry is made
				if not d.source_location and not (d.target_location or d.to_employee):
					frappe.throw(
						_("Target Location or To Employee is required while receiving Asset {0}").format(d.asset)
					)
				elif d.source_location:
					# when asset is received from an employee
					if d.target_location and not d.from_employee:
						frappe.throw(
							_("From employee is required while receiving Asset {0} to a target location").format(
								d.asset
							)
						)
					if d.from_employee and not d.target_location:
						frappe.throw(
							_("Target Location is required while receiving Asset {0} from an employee").format(d.asset)
						)
					if d.to_employee and d.target_location:
						frappe.throw(
							_(
								"Asset {0} cannot be received at a location and given to employee in a single movement"
							).format(d.asset)
						)

	def validate_employee(self):

		for d in self.borrowed_asset:
			if d.to_employee:
				current_custodian = frappe.db.get_value("SD Asset", d.asset, "custodian")
				current_employee = frappe.db.get_value("Employee", current_custodian, "employee_name")
				print(current_employee)
				if current_custodian != "" and current_custodian != d.to_employee:
					frappe.throw(_("The asset : {0} has been borrowed by the custodian : {1}. Please change in Purpose field to {2} if you want to borrow from another custodian").format(frappe.bold(d.asset),frappe.bold(current_employee),frappe.bold("Transfer")))

				else:
					self.assets = ""
					frappe.db.set_value('SD Asset', d.asset, 'custodian', d.to_employee)
					frappe.db.set_value('SD Asset', d.asset, 'status', 'Borrowed')

		for d in self.assets:
			if d.from_employee:
				current_custodian = frappe.db.get_value("SD Asset", d.asset, "custodian")
				current_employee = frappe.db.get_value("Employee", d.from_employee, "employee_name")
				belongs_to_employee = frappe.db.get_value("Employee", current_custodian, "employee_name")

				if current_custodian != "" and current_custodian != d.from_employee:
					frappe.throw(_("The asset : {0} does not belong to the custodian : {1}, it belongs to {2}").format(frappe.bold(d.asset),frappe.bold(current_employee),frappe.bold(belongs_to_employee)))

				else:
					self.borrowed_asset = ""
					frappe.db.set_value('SD Asset', d.asset, 'custodian', d.to_employee)
					frappe.db.set_value('SD Asset', d.asset, 'status', 'Borrowed')


			if d.to_employee and frappe.db.get_value("Employee", d.to_employee, "company") != self.company:
				frappe.throw(
					_("Employee {0} does not belongs to the company {1}").format(d.to_employee, self.company)
				)

	def on_submit(self):
		self.set_latest_location_in_asset()

	def on_cancel(self):
		self.set_latest_location_in_asset()

	def set_latest_location_in_asset(self):
		current_location, current_employee = "", ""
		cond = "1=1"

		for d in self.assets:
			args = {"asset": d.asset, "company": self.company}

			# latest entry corresponds to current document's location, employee when transaction date > previous dates
			# In case of cancellation it corresponds to previous latest document's location, employee
			latest_movement_entry = frappe.db.sql(
				"""
				SELECT asm_item.target_location, asm_item.to_employee
				FROM `tabAsset Movement Item` asm_item, `tabAsset Movement` asm
				WHERE
					asm_item.parent=asm.name and
					asm_item.asset=%(asset)s and
					asm.company=%(company)s and
					asm.docstatus=1 and {0}
				ORDER BY
					asm.transaction_date desc limit 1
				""".format(
					cond
				),
				args,
			)
			if latest_movement_entry:
				current_location = latest_movement_entry[0][0]
				current_employee = latest_movement_entry[0][1]

			frappe.db.set_value("Asset", d.asset, "location", current_location)
			frappe.db.set_value("Asset", d.asset, "custodian", current_employee)
