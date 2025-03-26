from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def apply_reward(self, reward):
        self.ensure_one()
        self.discount = reward.discount

        # If Avatax Amount has already been computed,
        # reset it to 0 so the user can recompute it
        if getattr(self, "tax_amt", 0) > 0:
            self.tax_amt = 0
            self.order_id.tax_amount = 0
