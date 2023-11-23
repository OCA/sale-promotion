from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleLoyaltyRewardWizard(models.TransientModel):
    _inherit = "sale.loyalty.reward.wizard"

    # In case of multi_gift reward
    multi_gift_reward = fields.Boolean(related="selected_reward_id.multi_gift")
    loyalty_multi_gift_ids = fields.One2many(
        related="selected_reward_id.loyalty_multi_gift_ids"
    )
    loyalty_gift_line_ids = fields.One2many(
        comodel_name="sale.loyalty.reward.product_line.wizard",
        inverse_name="wizard_id",
        compute="_compute_loyalty_gift_line_ids",
        store=True,
        readonly=False,
        string="Loyalty Gift Lines",
    )

    @api.depends("selected_reward_id")
    def _compute_loyalty_gift_line_ids(self):
        self.loyalty_gift_line_ids = None
        lines_vals = []
        if self.selected_reward_id.reward_type == "multi_gift":
            for line in self.loyalty_multi_gift_ids:
                lines_vals.append(
                    (
                        0,
                        0,
                        {
                            "wizard_id": self.id,
                            "reward_id": self.selected_reward_id.id,
                            "multi_gift_ids": [(6, 0, self.loyalty_multi_gift_ids.ids)],
                            "line_id": line.id,
                        },
                    )
                )
            self.loyalty_gift_line_ids = lines_vals

    def action_apply(self):
        self.ensure_one()
        if not self.selected_reward_id:
            raise ValidationError(_("No reward selected."))
        claimable_rewards = self.order_id._get_claimable_rewards()
        selected_coupon = False
        for coupon, rewards in claimable_rewards.items():
            if self.selected_reward_id in rewards:
                selected_coupon = coupon
                break
        if not selected_coupon:
            raise ValidationError(
                _(
                    "Coupon not found while trying to add the following reward: %s",
                    self.selected_reward_id.description,
                )
            )
        if self.selected_reward_id.reward_type == "multi_gift":
            reward_line_options = {}
            for line in self.loyalty_gift_line_ids:
                reward_line_options.update({line.line_id.id: line.selected_gift_id.id})
            order = self.env["sale.order"].browse(self.order_id.id)
            order.with_context(
                reward_line_options=reward_line_options
            )._apply_program_reward(self.selected_reward_id, coupon)
            order.with_context(
                reward_line_options=reward_line_options
            )._update_programs_and_rewards()
        else:
            return super().action_apply()
        return True


class SaleLoyaltyRewardProductLineWizard(models.TransientModel):
    _name = "sale.loyalty.reward.product_line.wizard"

    wizard_id = fields.Many2one(comodel_name="sale.loyalty.reward.wizard")
    reward_id = fields.Many2one(related="wizard_id.selected_reward_id", store=True)
    multi_gift_ids = fields.One2many(related="wizard_id.loyalty_multi_gift_ids")
    line_id = fields.Many2one(comodel_name="loyalty.reward.product_line")
    gift_ids = fields.Many2many(related="line_id.reward_product_ids")
    selected_gift_id = fields.Many2one(
        comodel_name="product.product",
        domain="[('id', 'in', gift_ids)]",
        compute="_compute_selected_gift_id",
        readonly=False,
        store=True,
    )

    @api.depends("gift_ids", "reward_id")
    def _compute_selected_gift_id(self):
        for wizard in self:
            if not wizard.wizard_id.selected_reward_id.reward_type == "multi_gift":
                wizard.selected_gift_id = None
            else:
                wizard.selected_gift_id = wizard.gift_ids[:1]
