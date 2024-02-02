# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _program_check_compute_points(self, programs):
        """Coupon incompatibility rules. Check the error strings for a detailed case
        detail."""
        self.ensure_one()
        result = super()._program_check_compute_points(programs)
        order_programs = self.order_line.reward_id.program_id
        for program in result:
            if any({x in order_programs for x in program.incompatible_promotion_ids}):
                result[program] = {
                    "error": _(
                        "This promotion is incompatible with other set already in the "
                        "order so it can't be applied."
                    )
                }
        return result
