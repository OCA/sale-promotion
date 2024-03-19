# Copyright 2021 Tecnativa - David Vidal
# Copyright 2021 Camptocamp - Silvio Gregorini
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = ["sale.order.line", "sale.coupon.refresh.mixin"]

    @api.model_create_multi
    def create(self, vals_list):
        if self._check_skip_refresh():
            return super().create(vals_list)

        self_ctx = self.with_context(skip_auto_refresh_coupons=True)
        lines = super(SaleOrderLine, self_ctx).create(vals_list)
        lines.order_id._auto_refresh_coupons()
        return lines

    def write(self, vals):
        if self._check_skip_refresh():
            return super().write(vals)

        old_data = self._read_recs_data()
        old_orders = self.order_id
        self_ctx = self.with_context(skip_auto_refresh_coupons=True)
        res = super(SaleOrderLine, self_ctx).write(vals)
        new_data = self._read_recs_data()
        new_orders = self.order_id
        # Until we restart Odoo, we won't get new triggers from params. Once restarted
        # the method will return an empty set.
        new_triggers = self._new_trigger()
        if old_data != new_data or any(x in new_triggers for x in vals):
            (old_orders | new_orders)._auto_refresh_coupons()
        return res

    def unlink(self):
        if self._check_skip_refresh():
            return super().unlink()

        orders = self.order_id
        self_ctx = self.with_context(skip_auto_refresh_coupons=True)
        res = super(SaleOrderLine, self_ctx).unlink()
        orders._auto_refresh_coupons()
        return res

    @api.model
    def _get_auto_refresh_coupons_triggers(self) -> set:
        triggers = super()._get_auto_refresh_coupons_triggers()
        triggers.update(
            {
                "discount",
                "product_id",
                "price_unit",
                "product_uom",
                "product_uom_qty",
                "tax_id",
            }
        )
        return triggers
