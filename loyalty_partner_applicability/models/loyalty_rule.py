# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class LoyaltyRule(models.Model):
    _name = "loyalty.rule"
    _inherit = ["loyalty.rule", "loyalty.partner.applicability.mixin"]

    def _is_partner_valid(self, partner):
        self.ensure_one()
        return super()._is_partner_valid(partner) and self.program_id._is_partner_valid(
            partner
        )
