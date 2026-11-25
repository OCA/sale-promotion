from odoo import models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"

    def _cart_update_order_line(self, order_line, quantity, **kwargs):
        res = super()._cart_update_order_line(order_line, quantity, **kwargs)
        # A referral code may have failed when the cart was still empty;
        # retry so the discount appears as soon as conditions are met.
        if self.referred_by_id and not self.code_enabled_rule_ids:
            self._apply_referral_code()
        return res
