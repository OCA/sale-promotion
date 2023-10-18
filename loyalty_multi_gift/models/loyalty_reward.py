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
    reward_type = fields.Selection(
        selection_add=[("multi_gift", "Multi Gift")],
        ondelete={"multi_gift": "set default"},
    )

    def name_get(self):
        """Add complete description for the multi gift reward type."""
        res = super().name_get()
        for reward in self.filtered(lambda x: x.program_type == "multi_gift"):
            reward_string = _("Free Products - %(name)s") % {
                "name": ", ".join(
                    f"{reward.reward_product_quantity}x "
                    f"{fields.first(reward.reward_product_ids).name}"
                    for reward in reward.loyalty_multi_gift_ids
                )
            }
            res.append((reward.id, reward_string))
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
        Another module like `sale_loyalty_selection_wizard` can dismiss it in order
        to allow optional"""
        for line in self:
            line.reward_default_product_id = fields.first(line.reward_product_ids)

    def _inverse_reward_default_product_id(self):
        for line in self.filtered("reward_default_product_id"):
            line.reward_product_ids = line.reward_default_product_id

    @api.onchange("reward_product_ids")
    def onchange_reward_product_ids(self):
        self.reward_default_product_id = fields.first(self.reward_product_ids)._origin
