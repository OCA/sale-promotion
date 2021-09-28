# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class SaleCouponReward(models.Model):
    _inherit = "sale.coupon.reward"

    reward_type = fields.Selection(selection_add=[("multiple_of", "Multiple of")])
    force_rewarded_product = fields.Boolean(
        help="Apply even if the rewarded product is not in the order lines",
    )
    reward_product_max_quantity = fields.Integer(
        string="Max reward quantity",
        default=0,
        help="Maximum reward product quantity (0 for no limit)",
    )

    def name_get(self):
        """Returns a complete description of the reward"""
        other_rewards = self.filtered(lambda x: x.reward_type != "multiple_of")
        result = super(SaleCouponReward, other_rewards).name_get()
        for reward in self - other_rewards:
            reward_string = _("Free Product - %s" % (reward.reward_product_id.name))
            result.append((reward.id, reward_string))
        return result
