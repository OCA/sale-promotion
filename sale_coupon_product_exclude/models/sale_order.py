# Copyright 2022 Dinar Gabbasov
# Copyright 2022 Ooops404
# Copyright 2022 Cetmix
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_base_order_lines(self, program):
        order_lines = super(SaleOrder, self)._get_base_order_lines(program)
        # exclude products from base order lines: the maximum discount cannot be greater than
        # the total sum of the base order lines with excluded products
        order_lines = order_lines.filtered(
            lambda line: not program._is_excluded_product(line.product_id)
        )
        return order_lines

    def _get_reward_values_discount(self, program):
        # we need to run the original method with the updated context
        # so that we can use the program to filter the order lines.
        return super(
            SaleOrder, self.with_context(current_coupon_program=program)
        )._get_reward_values_discount(program)

    def _get_paid_order_lines(self):
        order_lines = super(SaleOrder, self)._get_paid_order_lines()
        program = self.env.context.get("current_coupon_program")
        if program:
            order_lines = order_lines.filtered(
                lambda line: not program._is_excluded_product(line.product_id)
            )
        return order_lines

    def _get_cheapest_line(self):
        program = self.env.context.get("current_coupon_program")
        if program:
            return min(
                self.order_line.filtered(
                    lambda x: not x.is_reward_line
                    and x.price_reduce > 0
                    and not program._is_excluded_product(x.product_id)
                ),
                key=lambda x: x["price_reduce"],
            )
        else:
            return super(SaleOrder, self)._get_cheapest_line()

    def _get_reward_values_discount_percentage_per_line(self, program, line):
        if program._is_excluded_product(line.product_id):
            return False
        return super(SaleOrder, self)._get_reward_values_discount_percentage_per_line(
            program, line
        )
