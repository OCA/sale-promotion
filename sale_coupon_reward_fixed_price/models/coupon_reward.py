from odoo import _, fields, models


class CouponReward(models.Model):
    _inherit = "coupon.reward"

    reward_type = fields.Selection(selection_add=[("fixed_price", "Fixed Price")])
    price_unit = fields.Float(default=0)

    def name_get(self):
        """
        Override core method to change description for the reward with `domain_product`
        discount criterion
        """
        result = []
        reward_names = super(CouponReward, self).name_get()
        fixed_price_reward_ids = self.filtered(
            lambda reward: reward.reward_type == "fixed_price"
        ).ids
        for res in reward_names:
            result.append(
                (
                    res[0],
                    res[0] in fixed_price_reward_ids and _("Fixed Price") or res[1],
                )
            )
        return result
