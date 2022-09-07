from odoo import models


class SaleCouponApplyCode(models.TransientModel):
    _inherit = "sale.coupon.apply.code"

    def process_coupon(self):
        wiz = self.with_context(skip_auto_refresh_coupons=True)
        return super(SaleCouponApplyCode, wiz).process_coupon()

    def apply_coupon(self, order, coupon_code):
        """Avoid discarding the coupon before the end of the process"""
        return super().apply_coupon(
            order.with_context(skip_auto_refresh_coupons=True), coupon_code
        )
