# Copyright 2022 Ooops404
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class CouponReward(models.Model):
    _inherit = "coupon.reward"

    discount_apply_on = fields.Selection(
        selection_add=[("domain_product", "On Domain Matching Products")],
    )

    def name_get(self):
        discount_domain_product_rewards = self.filtered(
            lambda reward: reward.reward_type == "discount"
            and reward.discount_apply_on == "domain_product"
        )
        result = super(CouponReward, self - discount_domain_product_rewards).name_get()
        if discount_domain_product_rewards:
            result += [
                (
                    reward.id,
                    _(
                        "%s%% discount on selected products",
                        str(reward.discount_percentage),
                    ),
                )
                for reward in discount_domain_product_rewards
            ]
        return result
