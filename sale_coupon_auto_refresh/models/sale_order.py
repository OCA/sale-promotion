# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Used in UI to hide the manual button
    auto_refresh_coupon = fields.Boolean(related="company_id.auto_refresh_coupon",)

    def _auto_refresh_coupons(self):
        self.filtered(
            lambda x: x.state in ("draft", "sent") and x.auto_refresh_coupon
        ).recompute_coupon_lines()

    @api.model_create_multi
    def create(self, vals_list):
        """Create or refresh coupon lines on create"""
        orders = super().create(vals_list)
        orders.with_context(skip_auto_refresh_coupons=True)._auto_refresh_coupons()
        return orders

    def write(self, vals):
        """Create or refresh coupon lines after saving"""
        res = super().write(vals)
        if self.env.context.get("skip_auto_refresh_coupons"):
            return res
        self.with_context(skip_auto_refresh_coupons=True)._auto_refresh_coupons()
        return res
