# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class SaleCoupon(models.Model):
    _inherit = "sale.coupon"

    def _check_coupon_code(self, order):
        message = super()._check_coupon_code(order)
        if message:
            return message
        if self.program_id.reward_type == "multiple_of" and (
            not order._is_reward_in_order_lines(self.program_id)
            and self.force_rewarded_product
        ):
            message = {
                "error": _(
                    "The reward products should be in the sales order lines to "
                    "apply the discount."
                )
            }
        return message
