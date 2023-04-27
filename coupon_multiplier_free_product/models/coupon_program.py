# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    @api.onchange("reward_type")
    def _onchange_reward_type_multiple_of(self):
        """We don't want this flag active in other options"""
        if self.reward_type != "multiple_of":
            self.force_rewarded_product = False

    @api.onchange("reward_product_id")
    def _onchange_reward_product_multiple_of(self):
        """We need this to ensure some filters"""
        if self.reward_type == "multiple_of":
            self.discount_line_product_id = self.reward_product_id

    def _get_valid_products(self, products):
        if self.force_rewarded_product:
            return products.filtered(lambda x: x == self.reward_product_id)
        return super()._get_valid_products(products)
