# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import random

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command, first
from odoo.tools.float_utils import float_round


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_open_reward_wizard(self):
        self.ensure_one()
        self._update_programs_and_rewards()
        claimable_rewards = self._get_claimable_rewards()
        if (
            len(claimable_rewards) == 1
            and claimable_rewards.get(next(iter(claimable_rewards))).reward_type
            == "multi_gift"
            and any(
                len(record.reward_product_ids) > 1
                for record in claimable_rewards.get(
                    next(iter(claimable_rewards))
                ).loyalty_multi_gift_ids
            )
        ):
            ctx = {
                "default_selected_reward_id": claimable_rewards.get(
                    next(iter(claimable_rewards))
                ).id,
            }
            return {
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "sale.loyalty.reward.wizard",
                "target": "new",
                "context": ctx,
            }
        else:
            return super().action_open_reward_wizard()

    def _get_reward_values_multi_gift_line(
        self, reward, coupon, cost, reward_line=False, product=False
    ):
        """Multi Gift reward rules. For every gift reward rule, we'll create a new
        sale order line flagged as reward line with a 100% discount"""
        self.ensure_one()
        assert reward.reward_type == "multi_gift"
        selected_product = (
            self.env["product.product"].browse(
                self.env.context.get("reward_line_options", {}).get(reward_line.id)
            )
            & reward_line.reward_product_ids
        )
        reward_product_id = (
            selected_product or product or first(reward_line.reward_product_ids)
        )
        if (
            not reward_product_id
            or reward_product_id not in reward.loyalty_multi_gift_ids.reward_product_ids
        ):
            raise UserError(_("Invalid product to claim."))
        taxes = self.fiscal_position_id.map_tax(
            reward_product_id.taxes_id.filtered(
                lambda t: t.company_id == self.company_id
            )
        )
        vals = {
            "order_id": self.id,
            "is_reward_line": True,
            "name": _(
                "Free Product - %(product)s",
                product=reward_product_id.with_context(
                    display_default_code=False
                ).display_name,
            ),
            "product_id": reward_product_id.id,
            "price_unit": reward_product_id.list_price,
            "discount": 100,
            "product_uom_qty": reward_line.reward_product_quantity,
            "reward_id": reward.id,
            "coupon_id": coupon.id,
            "points_cost": cost,
            "reward_identifier_code": str(random.getrandbits(32)),
            "product_uom": reward_product_id.uom_id.id,
            "sequence": max(
                self.order_line.filtered(lambda x: not x.is_reward_line).mapped(
                    "sequence"
                ),
                default=10,
            )
            + 1,
            "tax_id": [(Command.CLEAR, 0, 0)]
            + [(Command.LINK, tax.id, False) for tax in taxes],
            "loyalty_program_id": reward.program_id.id,
            "multi_gift_reward_line_id": reward_line.id,
            "multi_gift_reward_line_id_option_product_id": reward_product_id.id,
        }
        return vals

    def _get_reward_values_multi_gift(self, reward, coupon, **kwargs):
        """Wrapper to create the reward lines for a multi gift promotion"""
        points = self._get_real_points_for_coupon(coupon)
        claimable_count = (
            float_round(
                points / reward.required_points,
                precision_rounding=1,
                rounding_method="DOWN",
            )
            if not reward.clear_wallet
            else 1
        )
        total_cost = (
            points if reward.clear_wallet else claimable_count * reward.required_points
        )
        cost = total_cost / len(reward.loyalty_multi_gift_ids)
        order_lines = self.order_line.filtered(
            lambda x: x.is_reward_line
            and x.reward_id.reward_type == "multi_gift"
            and x.coupon_id == coupon
        )
        if order_lines:
            return [
                self._get_reward_values_multi_gift_line(
                    reward,
                    coupon,
                    cost,
                    reward_line=reward_line.multi_gift_reward_line_id,
                    product=reward_line.multi_gift_reward_line_id_option_product_id,
                )
                for reward_line in order_lines
            ]
        else:
            return [
                self._get_reward_values_multi_gift_line(
                    reward, coupon, cost, reward_line=reward_line
                )
                for reward_line in reward.loyalty_multi_gift_ids
            ]

    def _get_reward_line_values(self, reward, coupon, **kwargs):
        """Hook into the core method considering multi gift rewards"""
        self.ensure_one()
        self = self.with_context(lang=self.partner_id.lang)
        reward = reward.with_context(lang=self.partner_id.lang)
        if reward.reward_type == "multi_gift":
            return self._get_reward_values_multi_gift(reward, coupon, **kwargs)
        return super()._get_reward_line_values(reward, coupon, **kwargs)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    multi_gift_reward_line_id = fields.Many2one(
        comodel_name="loyalty.reward.product_line",
        readonly=True,
    )
    multi_gift_reward_line_id_option_product_id = fields.Many2one(
        comodel_name="product.product",
        readonly=True,
    )
