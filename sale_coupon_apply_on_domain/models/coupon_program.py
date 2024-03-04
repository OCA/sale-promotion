# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import ast

from odoo import models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    def _filter_not_ordered_reward_programs(self, order):
        # Add matching product_domain programs
        programs = super()._filter_not_ordered_reward_programs(order)
        for program in programs:
            if (
                program.reward_type == "discount"
                and program.discount_apply_on == "product_domain"
            ):
                discount_domain_product_ids = program._get_discount_domain_product_ids(
                    order
                )
                if not order.order_line.filtered(
                    lambda line: line.product_id in discount_domain_product_ids
                ):
                    programs -= program
        return programs

    def _get_discount_domain_product_ids(self, order):
        # Return the product ids that match the discount_domain
        self.ensure_one()
        order_lines = (
            order.order_line.filtered(lambda line: line.product_id)
            - order._get_reward_lines()
        )
        products = order_lines.mapped("product_id")
        if self.discount_product_domain:
            domain = ast.literal_eval(self.discount_product_domain)
            return products.filtered_domain(domain)
        return self.env["product.product"]
