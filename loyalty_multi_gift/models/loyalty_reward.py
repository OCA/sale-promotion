# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models


class LoyaltyReward(models.Model):
    _inherit = "loyalty.reward"

    loyalty_multi_gift_ids = fields.One2many(
        comodel_name="loyalty.reward.product_line",
        inverse_name="reward_id",
        string="Gift list",
    )
    multi_gift = fields.Boolean(compute="_compute_multi_gift")
    reward_type = fields.Selection(
        selection_add=[("multi_gift", "Multi Gift")],
        ondelete={"multi_gift": "set default"},
    )

    @api.depends("reward_type", "loyalty_multi_gift_ids.reward_product_ids")
    def _compute_multi_gift(self):
        for reward in self:
            reward.multi_gift = (
                reward.reward_type == "multi_gift"
                and len(reward.loyalty_multi_gift_ids) > 0
            )

    @api.depends("loyalty_multi_gift_ids.reward_product_ids")
    def _compute_description(self):
        res = super()._compute_description()
        for reward in self:
            if reward.reward_type == "multi_gift":
                reward_string = ""
                products = self.env["product.product"].browse(
                    reward.loyalty_multi_gift_ids.reward_default_product_id.ids
                )
                product_names = products.with_context(
                    display_default_code=False
                ).mapped("display_name")
                if len(products) == 0:
                    reward_string = _("Multi Gift")
                else:
                    reward_string = _("Multi Gift - [%s]") % ", ".join(product_names)
                reward.description = reward_string
        return res


class LoyaltyGift(models.Model):
    _name = "loyalty.reward.product_line"
    _description = "Loyalty Multi Gift"

    reward_id = fields.Many2one(comodel_name="loyalty.reward")
    reward_product_quantity = fields.Integer(
        string="Quantity",
        help="Reward product quantity",
    )
    reward_default_product_id = fields.Many2one(
        comodel_name="product.product",
        compute="_compute_reward_default_product_id",
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
        Another module like `sale_loyalty_selection_wizard` can dismiss it in order
        to allow optional"""
        for line in self:
            line.reward_default_product_id = fields.first(line.reward_product_ids)

    @api.onchange("reward_product_ids")
    def onchange_reward_product_ids(self):
        self.reward_default_product_id = fields.first(self.reward_product_ids)._origin
