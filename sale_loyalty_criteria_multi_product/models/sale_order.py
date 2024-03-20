# Copyright 2021 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _program_check_compute_points(self, programs):
        res = super()._program_check_compute_points(programs)
        # Iterate through the programs that initially have no errors
        for program, result in res.items():
            if result.get("error", False):
                continue
            # Check that all rules have the criterion in place.
            if all(
                rule.loyalty_criteria == "multi_product" for rule in program.rule_ids
            ):
                order_products = self.order_line.filtered(
                    lambda x: not x.is_reward_line and x.product_uom_qty > 0
                ).mapped("product_id")
                # Check that at least one rule has all products in loyalty_criteria_ids
                # present in the order lines.
                if not any(
                    all(
                        product_id in order_products
                        for product_id in rule.loyalty_criteria_ids.product_ids
                    )
                    for rule in program.rule_ids
                ):
                    res[program] = {
                        "error": _(
                            "You don't have the required product quantities on your sales "
                            "order."
                        )
                    }
        return res
