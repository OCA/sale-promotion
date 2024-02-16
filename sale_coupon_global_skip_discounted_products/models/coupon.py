# Copyright 2021-2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, models


class CouponCoupon(models.Model):
    _inherit = "coupon.coupon"

    def _check_coupon_code(self, order):
        message = super()._check_coupon_code(order)
        if not message:
            return message

        if self.program_id._filtered_programs_on_products_for_skip_discounted_products(
            order
        ):
            message = {
                "error": _("The coupon code can't be applied on discounted products.")
            }
        return message
