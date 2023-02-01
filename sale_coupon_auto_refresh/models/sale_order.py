# Copyright 2021 Tecnativa - David Vidal
# Copyright 2021 Camptocamp - Silvio Gregorini
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


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
        orders = self.filtered(type(self)._allow_recompute_coupon_lines)
        if orders:
            orders = orders.with_context(skip_auto_refresh_coupons=True)
            orders.recompute_coupon_lines()

    def _allow_recompute_coupon_lines(self):
        """Returns whether reward lines in order ``self`` can be recomputed
        automatically.

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


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = ["sale.order.line", "sale.coupon.refresh.mixin"]

    @api.model_create_multi
    def create(self, vals_list):
        if self._check_skip_refresh():
            return super().create(vals_list)

        self_ctx = self.with_context(skip_auto_refresh_coupons=True)
        lines = super(SaleOrderLine, self_ctx).create(vals_list)
        lines.mapped("order_id")._auto_refresh_coupons()
        return lines

    def write(self, vals):
        if self._check_skip_refresh():
            return super().write(vals)

        old_data = self._read_recs_data()
        old_orders = self.mapped("order_id")
        self_ctx = self.with_context(skip_auto_refresh_coupons=True)
        res = super(SaleOrderLine, self_ctx).write(vals)
        new_data = self._read_recs_data()
        new_orders = self.mapped("order_id")
        # Until we restart Odoo, we won't get new triggers from params. Once restarted
        # the method will return an empty set.
        new_triggers = self._new_trigger()
        if old_data != new_data or any(x in new_triggers for x in vals):
            (old_orders | new_orders)._auto_refresh_coupons()
        return res

    def unlink(self):
        if self._check_skip_refresh():
            return super().unlink()

        orders = self.mapped("order_id")
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
