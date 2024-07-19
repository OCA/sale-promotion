# Copyright 2024 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _available_programs(self):
        self.ensure_one()
        filtered_programs = self._filter_programs_by_rules_with_products()
        programs_with_reward_multi_gift = filtered_programs.filtered(
            lambda x: any(reward.reward_type == "multi_gift" for reward in x.reward_ids)
        )
        programs = self.env["loyalty.program"]
        if programs_with_reward_multi_gift:
            product_id = self.env.context.get("product_id")
            programs += programs_with_reward_multi_gift.filtered(
                lambda x: any(
                    product_id in reward.loyalty_multi_gift_ids.reward_product_ids.ids
                    for reward in x.reward_ids
                )
            )
        return super()._available_programs() + programs
