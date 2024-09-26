# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class LoyaltyRule(models.Model):
    _inherit = "loyalty.rule"
    _description = "Loyalty Rule"

    rule_partners_domain = fields.Char(
        string="Based on Customers",
        help="Loyalty program will work for selected customers only",
        default="[]",
    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for vals in vals_list:
            if not vals.get("rule_partners_domain", False):
                vals["rule_partners_domain"] = "[]"
        return res
