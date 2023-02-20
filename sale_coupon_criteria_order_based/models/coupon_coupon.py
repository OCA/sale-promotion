# Copyright 2022 Ooops404
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models


class CouponCoupon(models.Model):
    _inherit = "coupon.coupon"

    def _check_coupon_code(self, order_date, partner_id, **kwargs):
        message = super()._check_coupon_code(order_date, partner_id, **kwargs)
        order = kwargs.get("order")
        if not self.program_id._is_valid_order(order):
            message = {"error": _("The order doesn't have access to this reward.")}
        return message
