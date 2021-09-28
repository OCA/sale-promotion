# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class SaleCoupon(models.Model):
    _inherit = "sale.coupon.program"

    website_only = fields.Boolean(
        string="Only for e-commerce",
        help="Check this if the coupon can only be validated from the e-commerce.",
    )

    def _check_promo_code(self, order, coupon_code):
        if self.website_only and not order.website_id:
            return {"error": _("This coupon can only be validated on the e-commerce")}
        return super()._check_promo_code(order, coupon_code)
