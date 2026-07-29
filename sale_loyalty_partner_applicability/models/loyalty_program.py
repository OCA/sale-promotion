# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    def _get_valid_products(self, products):
        current_so = self.env.context.get("order")
        # The order is set into the context by the sale order line
        # when the method _program_check_compute_points is called.
        # This allows to check the partner of the order and filter
        # the rules based on the partner domain.
        valid_programs = self
        if current_so:
            applicable_partner = (
                current_so._get_applicable_partner_for_loyalty_program()
            )
            valid_programs = self.filtered(
                lambda p: p._is_partner_valid(applicable_partner)
            )
        return super(LoyaltyProgram, valid_programs)._get_valid_products(products)
