# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines.mapped('order_id').recompute_coupon_lines()
        return lines

    def write(self, vals):
        def _snapshot():
            return {
                d['id']: {k: v for k, v in d.items() if k != 'id'}
                for d in self.read(tracked_fields, load='')
            }

        def _is_updated(rec):
            return old_data.get(rec.id) != new_data.get(rec.id)

        tracked_fields = self._get_tracked_fields_to_recompute_rewards()
        old_data = _snapshot()
        res = super().write(vals)
        new_data = _snapshot()
        updated_lines = self.filtered(_is_updated)
        if updated_lines:
            updated_lines.mapped('order_id').recompute_coupon_lines()
        return res

    def unlink(self):
        orders = self.mapped('order_id')
        res = super().unlink()
        orders.recompute_coupon_lines()
        return res

    @api.model
    def _get_tracked_fields_to_recompute_rewards(self) -> list:
        """To avoid performance issues, reward lines will be recomputed only
        if a given subset of sale.order.line field values has been updated
        when :meth:`write` is called.
        This method can be used as a hook to override the list of fields that
        needs to be tracked.

        :return: a list of sale.order.line field names
        """
        return [
            'order_id',
            'price_unit',
            'product_id',
            'product_uom',
            'product_uom_qty',
        ]
