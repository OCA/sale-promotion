# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _set_reward_fixed_price_for_lines(self, program):
        lines = super()._set_reward_fixed_price_for_lines(program)
        if lines:
            lines.write({"coupon_program_id": program.id})
        return lines
