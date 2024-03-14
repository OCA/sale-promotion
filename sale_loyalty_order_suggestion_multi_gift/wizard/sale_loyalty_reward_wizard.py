from odoo import models


class SaleLoyaltyRewardWizard(models.TransientModel):
    _inherit = "sale.loyalty.reward.wizard"

    def action_apply(self):
        res = super().action_apply()
        # It's necessary to adjust the order line when suggestions are made on order
        # lines that contain products that are part of a multi-gift reward, i.e. if product A is
        # added to the order and a promotion is suggested that has product A as a reward,
        # that order line will become an order reward line or the quantity indicated in
        # the promotion reward.
        if self.multi_gift_reward:
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


class SaleLoyaltyRewardProductLineWizard(models.TransientModel):
    _inherit = "sale.loyalty.reward.product_line.wizard"

    def _compute_selected_gift_id(self):
        res = super()._compute_selected_gift_id()
        for wizard in self:
            if (
                wizard.wizard_id.multi_gift_reward
                and wizard.wizard_id.product_id in wizard.gift_ids._origin
            ):
                wizard.selected_gift_id = wizard.wizard_id.product_id
        return res
