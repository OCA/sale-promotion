# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class SaleCoupon(models.Model):
    _inherit = "coupon.coupon"

    def _check_coupon_code(self, order_date, partner_id, **kwargs):
        order = kwargs.get("order", False)
        if order and self.program_id.website_only and not order.website_id:
            return {"error": _("This coupon can only be used in the e-commerce")}
        return super()._check_coupon_code(order_date, partner_id, **kwargs)
