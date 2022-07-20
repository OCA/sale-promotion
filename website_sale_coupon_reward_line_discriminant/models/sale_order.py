# Copyright 2021 Domatix - Álvaro López
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_find_product_line(self, product_id=None, line_id=None, **kwargs):
        lines = super()._cart_find_product_line(product_id, line_id, **kwargs)
        lines = lines.filtered(lambda r: not r.is_reward_line)
        return lines
