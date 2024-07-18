from odoo import models


class SaleLoyaltyRewardWizard(models.TransientModel):
    _inherit = "sale.loyalty.reward.wizard"

    def action_apply(self):
        """Avoid discarding the coupon before the end of the process"""
        return super(
            SaleLoyaltyRewardWizard, self.with_context(skip_auto_refresh_coupons=True)
        ).action_apply()
