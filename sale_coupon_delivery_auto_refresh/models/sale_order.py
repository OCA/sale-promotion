# Copyright 2022 Cetmix
# Copyright 2022 Ooops404
# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _auto_refresh_delivery(self):
        """When refreshing delivery lines skip coupons auto compute"""
        return super(
            SaleOrder, self.with_context(skip_auto_refresh_coupons=True)
        )._auto_refresh_delivery()

    def recompute_coupon_lines(self):
        """When refreshing promotions skip delivery lines auto compute"""
        return super(
            SaleOrder, self.with_context(auto_refresh_delivery=True)
        ).recompute_coupon_lines()
