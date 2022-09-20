from odoo import models


class Picking(models.Model):
    _inherit = "stock.picking"

    def _update_sale_delivered_coupon_lines_quantity(self):
        self.sale_id._update_delivered_coupon_lines_quantity()

    def _action_done(self):
        # FIXME: Avoid calling _update_delivered_coupon_lines_quantity
        # several times on the same picking
        rv = super()._action_done()

        if self.sale_id._get_applied_programs_with_rewards_on_current_order().filtered(
            lambda program: program.invoice_on_delivered
        ):
            self._update_sale_delivered_coupon_lines_quantity()

        return rv
