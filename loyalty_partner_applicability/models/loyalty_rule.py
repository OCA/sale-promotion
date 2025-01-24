# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import ast

from odoo import api, fields, models
from odoo.osv import expression


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

    def _get_partner_domain(self, partner):
        self.ensure_one()
        domain = []
        if self.rule_partners_domain and self.rule_partners_domain != "[]":
            allow_sharing = (
                self.env["ir.config_parameter"].sudo().get_param("allow_coupon_sharing")
            )
            if (
                allow_sharing
                and allow_sharing.lower() == "true"
                or allow_sharing == "1"
            ):
                domain = [
                    ("commercial_partner_id", "=", partner.commercial_partner_id.id)
                ]
            else:
                domain = [("id", "=", partner.id)]
            domain = expression.AND(
                [ast.literal_eval(self.rule_partners_domain), domain]
            )
        return domain

    def _is_partner_valid(self, partner):
        self.ensure_one()
        partner_domain = self._get_partner_domain(partner)
        return self.env["res.partner"].search_count(partner_domain)
