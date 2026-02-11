# Copyright (C) 2023 Open Source Integrators (https://www.opensourceintegrators.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _get_attributes_by_ptal_id(self):
        res = super(PosSession, self)._get_attributes_by_ptal_id()
        for _key, values in res.items():
            for attribute_value in values["values"]:
                line = self.env["product.attribute.value"].browse(attribute_value["id"])
                attribute_value.update({"attribute_id": line.attribute_id.id})
        return res

    def _loader_params_loyalty_reward(self):
        result = super()._loader_params_loyalty_reward()
        result["search_params"]["fields"].append("limit_discounted_attributes")
        result["search_params"]["fields"].append("discount_attribute_ids")
        return result
