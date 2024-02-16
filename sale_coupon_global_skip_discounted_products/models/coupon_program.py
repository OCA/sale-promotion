# Copyright 2021-2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    skip_discounted_products = fields.Boolean(
        "Skip discounted products",
        default=False,
        help="Allow this program to skip discounted products.",
    )

    def _filter_programs_on_products(self, order):
        valid_programs = super()._filter_programs_on_products(order)
        return self._filter_programs_on_products_with_skip_discounted_products(
            order, valid_programs
        )

    def _filter_programs_on_products_with_skip_discounted_products(
        self, order, valid_programs
    ):
        order_lines = (
            order.order_line.filtered(lambda line: line.product_id)
            - order._get_reward_lines()
        )

        nonrelevant_programs = self.env["coupon.program"]

        for program in valid_programs:
            if program.skip_discounted_products:
                relevant_lines = order_lines.filtered(
                    lambda line: program._is_valid_product(line.product_id)
                )
                if all(line.discount > 0 for line in relevant_lines):
                    nonrelevant_programs |= program

        return valid_programs - nonrelevant_programs

    def _filtered_programs_on_products_for_skip_discounted_products(self, order):
        valid_programs = super()._filter_programs_on_products(order)

        skipped_programs = (
            self._filter_programs_on_products_with_skip_discounted_products(
                order, valid_programs
            )
        )

        return valid_programs - skipped_programs

    def _check_promo_code(self, order, coupon_code):
        message = super()._check_promo_code(order, coupon_code)
        if not message:
            return message

        if self._filtered_programs_on_products_for_skip_discounted_products(order):
            message = {
                "error": _("The coupon code can't be applied on discounted products.")
            }
        return message
