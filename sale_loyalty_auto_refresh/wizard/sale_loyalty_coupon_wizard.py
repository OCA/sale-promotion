from odoo import models


class SaleLoyaltyCouponWizard(models.TransientModel):
    _inherit = "sale.loyalty.coupon.wizard"

    def action_apply(self):
        """Avoid discarding the coupon before the end of the process"""
        return super(
            SaleLoyaltyCouponWizard, self.with_context(skip_auto_refresh_coupons=True)
        ).action_apply()
