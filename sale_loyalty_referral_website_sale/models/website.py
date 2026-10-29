from odoo import models


class Website(models.Model):
    _inherit = "website"

    def _create_cart(self):
        # A cart created in a referral session keeps the referrer and gets the
        # code applied at once, so the discount shows at checkout.
        order = super()._create_cart()
        referrer = self.env["res.partner"]._get_referral_partner()
        if referrer and not order.referred_by_id:
            order.referred_by_id = referrer.id
            order._apply_referral_code()
        return order
