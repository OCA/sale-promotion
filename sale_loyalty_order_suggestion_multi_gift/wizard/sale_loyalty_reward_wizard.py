from odoo import models


class SaleLoyaltyRewardWizard(models.TransientModel):
    _inherit = "sale.loyalty.reward.wizard"

    def action_apply(self):
        res = super().action_apply()
        if self.selected_reward_id.reward_type == "multi_gift":
            for gift_line in self.loyalty_gift_line_ids:
                selected_product = gift_line.selected_gift_id
                product_qty = gift_line.line_id.reward_product_quantity
                order_line = self.order_id.order_line.filtered(
                    lambda x: x.product_id == selected_product and not x.is_reward_line
                )
                units_to_include = (
                    self.loyalty_rule_line_ids.filtered(
                        lambda x: x.product_id == selected_product
                    ).units_to_include
                    or False
                )
                if not units_to_include:
                    update_qty = order_line.product_uom_qty - product_qty
                    if update_qty < 1:
                        order_line.unlink()
                    else:
                        self._update_order_line_with_units(order_line, -abs(update_qty))
        return res
