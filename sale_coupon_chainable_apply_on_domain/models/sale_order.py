# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _filter_lines_rewarded_for_program_on_specific_products(self, lines, program):
        # We need to filter out the lines that are not on the same
        # product domain as the current program
        if program.discount_apply_on != "product_domain":
            return super()._filter_lines_rewarded_for_program_on_specific_products(
                lines, program
            )

        discount_specific_product_ids = program._get_discount_domain_product_ids(self)

        free_product_lines = (
            self.env["coupon.program"]
            .search(
                [
                    ("reward_type", "=", "product"),
                    (
                        "reward_product_id",
                        "in",
                        discount_specific_product_ids.ids,
                    ),
                ]
            )
            .mapped("discount_line_product_id")
        )
        lines = lines.filtered(
            lambda x: x.product_id
            in (discount_specific_product_ids | free_product_lines)
        )

        return lines
