# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models


class CouponReward(models.Model):
    _inherit = "coupon.reward"

    coupon_multi_gift_ids = fields.One2many(
        comodel_name="coupon.reward.product_line",
        inverse_name="reward_id",
        string="Gift list",
    )
    reward_type = fields.Selection(selection_add=[("multi_gift", "Multi Gift")])

    def name_get(self):
        """Add complete description for the multi gift reward type."""
        res = super().name_get()
        for reward in self.filtered(lambda x: x.reward_type == "multi_gift"):
            reward_string = _(
                "Free Products - %s"
                % (
                    ", ".join(
                        "{}x {}".format(
                            reward.reward_product_quantity,
                            fields.first(reward.reward_product_ids).name,
                        )
                        for reward in reward.coupon_multi_gift_ids
                    )
                )
            )
            res.append((reward.id, reward_string))
        return res


class CouponGift(models.Model):
    _name = "coupon.reward.product_line"
    _description = "Coupon Multi Gift"

    reward_id = fields.Many2one(comodel_name="coupon.reward")
    reward_product_quantity = fields.Integer(
        string="Quantity",
        help="Reward product quantity",
    )
    reward_default_product_id = fields.Many2one(
        comodel_name="product.product",
        compute="_compute_reward_default_product_id",
        inverse="_inverse_reward_default_product_id",
        readonly=False,
    )
    reward_product_ids = fields.Many2many(
        comodel_name="product.product",
        string="Gift Options",
        help="Reward Product",
    )

    @api.depends("reward_product_ids")
    def _compute_reward_default_product_id(self):
        """This field acts as a cover for a simple many2one behavior of the module.
        Another module like `sale_coupon_selection_wizard` can dismiss it in order
        to allow optional"""
        for line in self:
            line.reward_default_product_id = fields.first(line.reward_product_ids)

    def _inverse_reward_default_product_id(self):
        for line in self.filtered("reward_default_product_id"):
            line.reward_product_ids = line.reward_default_product_id

    @api.onchange("reward_product_ids")
    def onchange_reward_product_ids(self):
        self.reward_default_product_id = fields.first(self.reward_product_ids)._origin
