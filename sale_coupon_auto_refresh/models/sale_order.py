# Copyright 2021 Tecnativa - David Vidal
# Copyright 2021 Camptocamp - Silvio Gregorini
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Used in UI to hide the manual button
    auto_refresh_coupon = fields.Boolean(
        related="company_id.auto_refresh_coupon",
    )

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._auto_refresh_coupons()
        return orders

    def write(self, vals):
        res = super().write(vals)
        self._auto_refresh_coupons()
        return res

    def _auto_refresh_coupons(self):
        if not self.env.context.get("skip_auto_refresh_coupons"):
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


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines.mapped("order_id")._auto_refresh_coupons()
        return lines

    def write(self, vals):
        orders = self.mapped("order_id")
        res = super().write(vals)
        orders |= self.mapped("order_id")
        orders._auto_refresh_coupons()
        return res

    def unlink(self):
        orders = self.mapped("order_id")
        res = super().unlink()
        orders._auto_refresh_coupons()
        return res
