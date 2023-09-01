# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_reward_values_discount(self, reward, coupon, **kwargs):
        # recalculates the reward discount
        #
        self.ensure_one()
        res = super()._get_reward_values_discount(reward, coupon, **kwargs)
        LoyaltyReward = self.env["loyalty.reward"]
        i = 0  # sets an index for res
        for discount in res:
            price_unit = discount.get("price_unit")
            reward = LoyaltyReward.browse(discount.get("reward_id"))
            discount_value = (
                reward.discount / 100
            )  # implies that discount is a percentage
            # if product has an attribute selected on the discount
            reward_attributes = reward.discount_attribute_ids
            # get the matching sale order lines for the current discount
            if (
                reward.limit_discounted_attributes
                and reward.limit_discounted_attributes != "disabled"
            ):
                attributes_wise_price_unit = 0.0
                for so_lines in self.order_line.filtered(
                    lambda l: not l.reward_id
                    and l.product_id.id in reward.discount_product_ids.ids
                ):
                    for (
                        value_line
                    ) in so_lines.product_no_variant_attribute_value_ids.filtered(
                        lambda l: l.attribute_id not in reward_attributes
                    ):
                        attributes_wise_price_unit += (
                            value_line.price_extra * discount_value
                        )
                    # if limit discounted attributes is set to attributes,
                    # sales list price should not be considered for discount as well
                    # and is counted as many times as the product repeats itself in the lines
                    if reward.limit_discounted_attributes == "attributes":
                        price_unit += (
                            so_lines.product_id.list_price
                            * len(so_lines)
                            * discount_value
                        )
                price_unit = -(abs(price_unit) - attributes_wise_price_unit)
                discount.update({"price_unit": price_unit})
                # replaces the discount line
                res[i] = discount
                i += 1  # increments the index for res

        return res
