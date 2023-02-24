# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_applicable_no_code_promo_program(self):
        """Override to pass the context in the coupon.program `search` method"""
        return super(
            SaleOrder, self.with_context(discard_no_code_programs_with_code=True)
        )._get_applicable_no_code_promo_program()

    def write(self, vals):
        """Store code programs along with automatic programs"""
        if self.env.context.get("apply_no_code_as_code") and vals.get(
            "code_promo_program_id"
        ):
            program_id = vals.pop("code_promo_program_id")
            vals["no_code_promo_program_ids"] = [(4, program_id)]
        return super().write(vals)
