# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _program_check_compute_points(self, programs):
        """
        Updates applied programs's given points with the current state of the order.
        Checks automatic programs for applicability.
        Updates applied rewards using the new points and the current state of the order
        (for example with % discounts).
        """
        self.ensure_one()
        domain_programs = programs.filtered(lambda x: x.loyalty_criteria == "domain")
        multi_product_programs = (programs - domain_programs).filtered(
            "loyalty_criteria_ids"
        )
        # We'll return them altogether
        valid_domain_criteria_programs = super()._program_check_compute_points(
            domain_programs
        )
        order_lines = self.order_line.filtered(
            lambda line: line.product_id
        ) - self.order_line.filtered("is_reward_line")
        products = order_lines.mapped("product_id")
        products_qties = dict.fromkeys(products, 0)
        for line in order_lines:
            products_qties[line.product_id] += line.product_uom_qty
        valid_multi_product_criteria_programs = dict.fromkeys(
            multi_product_programs, dict()
        )

        for program in multi_product_programs:
            criterias_are_valid = True
            for criteria in program.loyalty_criteria_ids:
                valid_products = program._get_valid_products_multi_product(
                    products, criteria
                )
                if not valid_products:
                    criterias_are_valid = False
                ordered_rule_products_qty = sum(
                    products_qties[p] for p in valid_products
                )
                if ordered_rule_products_qty < criteria.criterian_min_quantity:
                    criterias_are_valid = False
            if not criterias_are_valid:
                valid_multi_product_criteria_programs[program] = {
                    "error": "You don't have the required "
                    "product quantities on your sales order."
                }
            else:
                # bypass: forced the points of program
                # because the original function takes this from rules
                valid_multi_product_criteria_programs[program] = {"points": [1]}
        return {
            **valid_domain_criteria_programs,
            **valid_multi_product_criteria_programs,
        }
