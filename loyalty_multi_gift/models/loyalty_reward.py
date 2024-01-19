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

    def write(self, vals):
        """Avoid duplicating the multi gift lines when updating the reward"""
        if self.env.context.get("skip_muli_gift_updates") and vals.get(
            "loyalty_multi_gift_ids"
        ):
            del vals["loyalty_multi_gift_ids"]
            self.env.context = dict(self.env.context, skip_muli_gift_updates=False)
        return super().write(vals)


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    def write(self, vals):
        """In https://github.com/odoo/odoo/blob/69b1993fb45b76110c24f5189a0ecfe9eb59a2aa
        /addons/loyalty/models/loyalty_program.py#L409
        there is a call convert_to_cache on reward_ids that causes that one2many create
        commands are called twice and thus we get a duplicated record."""
        reward_vals = vals.get("reward_ids", [])
        skip_muli_gift_updates = any(
            [
                cmd
                for cmd in reward_vals
                if len(cmd) == 3
                and cmd[0] == 1
                and cmd[2].get("loyalty_multi_gift_ids")
            ]
        )
        if skip_muli_gift_updates:
            self = self.with_context(skip_muli_gift_updates=True)
        return super().write(vals)


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
