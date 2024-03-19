# Copyright 2021 Tecnativa - David Vidal
# Copyright 2021 Camptocamp - Silvio Gregorini
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "sale.coupon.refresh.mixin"]

    # Used in UI to hide the manual button
    auto_refresh_coupon = fields.Boolean(
        related="company_id.auto_refresh_coupon",
    )

    @api.model_create_multi
    def create(self, vals_list):
        if self._check_skip_refresh():
            return super().create(vals_list)

        self_ctx = self.with_context(skip_auto_refresh_coupons=True)
        orders = super(SaleOrder, self_ctx).create(vals_list)
        orders._auto_refresh_coupons()
        return orders

    def write(self, vals):
        if self._check_skip_refresh():
            return super().write(vals)

        old_data = self._read_recs_data()
        self_ctx = self.with_context(skip_auto_refresh_coupons=True)
        res = super(SaleOrder, self_ctx).write(vals)
        new_data = self._read_recs_data()
        # Until we restart Odoo, we won't get new triggers from params. Once restarted
        # the method will return an empty set.
        new_triggers = self._new_trigger()
        if old_data != new_data or any(x in new_triggers for x in vals):
            self._auto_refresh_coupons()
        return res

    def _auto_refresh_coupons(self):
        orders = self.with_context(skip_auto_refresh_coupons=True).filtered(
            type(self)._allow_recompute_coupon_lines
        )
        for order in orders:
            order._update_programs_and_rewards()
            order.action_apply_rewards()

    def action_apply_rewards(self):
        self.ensure_one()
        claimable_rewards = self._get_claimable_rewards()
        for coupon, reward in claimable_rewards.items():
            try:
                self._apply_program_reward(reward, coupon)
                self._update_programs_and_rewards()
            except (UserError, ValidationError) as e:
                # Ignore exception errors to unblock the user when creating/writing
                logger.debug(e)

    def _allow_recompute_coupon_lines(self):
        """Check  if reward lines in ``self`` can be recomputed automatically.

        Hook method, to be overridden for custom behaviours.

        :return: True if the current SO allows automatic recomputation for
        reward lines, False otherwise.
        """
        self.ensure_one()
        return self.auto_refresh_coupon and self.state in ("draft", "sent")

    @api.model
    def _get_auto_refresh_coupons_triggers(self) -> set:
        triggers = super()._get_auto_refresh_coupons_triggers()
        triggers.update(
            {
                "order_line.auto_refresh_coupon_triggers_data",
                "partner_id",
            }
        )
        return triggers

    def action_open_reward_wizard(self):
        return super(
            SaleOrder, self.with_context(skip_auto_refresh_coupons=True)
        ).action_open_reward_wizard()

    def _update_programs_and_rewards(self):
        return super(
            SaleOrder, self.with_context(skip_auto_refresh_coupons=True)
        )._update_programs_and_rewards()
