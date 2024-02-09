# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class CDAssetSarpras(Document):
    def before_save(self):
        self.validate_condition_asset()

    def validate_condition_asset(self):
        for assets in self.assets:
            cd_asset = frappe.db.get_value("CD Asset", assets.asset_name, ["condition", "status", "asset_name"], as_dict=1)
            if not cd_asset.condition == "Good":
                frappe.throw(_("The asset : {0} cannot be borrowed, because current asset condition is {1}").format(frappe.bold(cd_asset.asset_name), frappe.bold(cd_asset.condition)))