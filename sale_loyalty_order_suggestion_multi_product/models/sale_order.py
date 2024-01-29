# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _filter_programs_by_rules_with_products(self):
        res = super()._filter_programs_by_rules_with_products()
        valid_programs = self._get_available_programs()
        # Filters programs that have rules multi_product
        programs_with_criteria_multi_product = valid_programs.filtered(
            lambda x: any(
                rule.loyalty_criteria == "multi_product" for rule in x.rule_ids
            )
        )
        return res + (programs_with_criteria_multi_product - res)

    def _available_programs(self):
        self.ensure_one()
        filtered_programs = self._filter_programs_by_rules_with_products()
        programs = self.env["loyalty.program"]
        if filtered_programs:
            product_id = self.env.context.get("product_id")
            programs += filtered_programs.filtered(
                lambda x: any(
                    product_id in rule.loyalty_criteria_ids.product_ids.ids
                    for rule in x.rule_ids
                )
            )
        return super()._available_programs() + programs
