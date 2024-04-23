from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _auto_refresh_delivery(self):
        """
        Override to change context value to refresh coupons after creation
        delivery line
        """
        self = self.with_context(
            skip_auto_refresh_coupons=False, auto_refresh_delivery=True
        )
        return super(SaleOrder, self)._auto_refresh_delivery()

    def _create_delivery_line(self, carrier, price_unit):
        """
        Override to refresh coupons after creation delivery line
        """
        if self._check_skip_refresh():
            return super()._create_delivery_line(carrier, price_unit)
        self_ctx = self.with_context(skip_auto_refresh_coupons=True)
        sol = super(SaleOrder, self_ctx)._create_delivery_line(carrier, price_unit)
        self._auto_refresh_coupons()
        return sol

    def copy(self, default=None):
        return super(
            SaleOrder,
            self.with_context(
                skip_auto_refresh_coupons=True, auto_refresh_delivery=True
            ),
        ).copy(default)

    def copy_data(self, default=None):
        vals_list = super().copy_data(default)
        for vals in vals_list:
            order_line = vals.get("order_line")
            if order_line:
                order_line = [
                    i
                    for i in order_line
                    if not (i[2].get("is_reward_line") or i[2].get("is_delivery"))
                ]
                vals["order_line"] = order_line
        return vals_list
