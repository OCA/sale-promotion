# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class SaleCouponReward(models.Model):
    _inherit = "sale.coupon.reward"

    coupon_multi_gift_ids = fields.One2many(
        comodel_name="sale.coupon.reward.product_line",
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
                        reward.reward_product_id.name
                        for reward in reward.coupon_multi_gift_ids
                    )
                )
            )
            res.append((reward.id, reward_string))
        return res


class SaleCouponGift(models.Model):
    _name = "sale.coupon.reward.product_line"
    _description = "Coupon Multi Gift"

    reward_id = fields.Many2one(comodel_name="sale.coupon.reward")
    reward_product_quantity = fields.Integer(
        string="Quantity", help="Reward product quantity",
    )
    reward_product_id = fields.Many2one(
        comodel_name="product.product", string="Free Product", help="Reward Product",
    )
    reward_product_uom_id = fields.Many2one(
        related="reward_product_id.product_tmpl_id.uom_id",
        string="Unit of Measure",
        readonly=True,
    )
