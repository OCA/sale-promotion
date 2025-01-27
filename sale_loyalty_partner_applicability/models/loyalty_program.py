# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    def _get_valid_products(self, products):
        rule_products = super()._get_valid_products(products)
        current_so = self.env.context.get("order")
        # The order is set into the context by the sale order line
        # when the method _program_check_compute_points is called.
        # This allows to check the partner of the order and filter
        # the rules based on the partner domain.
        if current_so:
            applicable_partner = (
                current_so._get_applicable_partner_for_loyalty_program()
            )
            new_rule_products = {}
            for rule, rule_product in rule_products.items():
                # we only check applicability if a product is set
                if rule_product and rule._is_partner_valid(applicable_partner):
                    new_rule_products[rule] = rule_product
                else:
                    new_rule_products[rule] = self.env["product.product"]
            rule_products = new_rule_products
        return rule_products
