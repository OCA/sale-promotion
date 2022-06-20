from odoo import models


class Picking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        # FIXME: Avoid calling recompute_coupon_lines several times on the same picking
        rv = super()._action_done()
        if self.sale_id._get_applied_programs_with_rewards_on_current_order().filtered(
            lambda program: program.invoice_on_delivered
        ):
            self.sale_id.recompute_coupon_lines()

        return rv
