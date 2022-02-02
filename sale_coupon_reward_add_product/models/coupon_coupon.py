# Copyright 2022 Camptocamp SA (https://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class CouponCoupon(models.Model):
    _inherit = "coupon.coupon"

    def _check_coupon_code(self, order):
        # OVERRIDE to skip the _is_reward_in_order_lines check
        if self.program_id.reward_product_add_if_missing:
            order = order.with_context(check_reward_in_order_lines=False)
        return super()._check_coupon_code(order)
