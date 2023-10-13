# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    def _get_valid_products_multi_product(self, products, rule):
        """Return valid products depending on the rule repeat product setting. Then
        the main method will check if the minimum quantities are acomplished."""
        if rule.repeat_product:
            return products.browse([x.id for x in rule.product_ids if x in products])
        if not all([x in products for x in rule.product_ids]):
            return self.env["product.product"]
        return rule.product_ids
