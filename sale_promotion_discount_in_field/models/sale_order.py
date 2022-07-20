# Copyright 2022 Ooops404
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_reward_line_values(self, program):
        """
        Overrider core method to set discount for line if program has
        'discount_line' reward type
        """
        if program.reward_type == "discount_line":
            self._set_reward_discount_for_lines(program)
            return []
        return super()._get_reward_line_values(program)

    def _set_reward_discount_for_lines(self, program):
        """
        Set discount for order lines
        """
        if program.discount_apply_on == "cheapest_product":
            lines = self._get_cheapest_line()
        else:
            lines = self._get_discount_in_field_lines(program)
        lines.discount = program.discount_percentage

    def _get_discount_in_field_lines(self, program):
        """
        Return lines related with the program to apply discount
        """
        lines = self._get_paid_order_lines()
        if program.discount_apply_on == "specific_products":
            free_product_lines = (
                self.env["coupon.program"]
                .search(
                    [
                        ("reward_type", "=", "product"),
                        (
                            "reward_product_id",
                            "in",
                            program.discount_specific_product_ids.ids,
                        ),
                    ],
                )
                .mapped("discount_line_product_id")
            )
            lines = lines.filtered(
                lambda x: x.product_id
                in (program.discount_specific_product_ids | free_product_lines),
            )
        return lines

    def _update_existing_reward_lines(self):
        """
        Override method to add context to ignore programs with reward type is discount_line
        and update discount of lines
        """
        self.ensure_one()
        res = super(
            SaleOrder,
            self.with_context(ignore_reward_type_with_discount_line=True),
        )._update_existing_reward_lines()
        order = self
        applied_discount_programs = (
            order._get_applied_programs_with_rewards_on_current_order().filtered(
                lambda program: program.reward_type == "discount_line",
            )
        )
        for program in applied_discount_programs:
            lines = (self.order_line - self._get_reward_lines()).filtered(
                lambda line: program._get_valid_products(line.product_id),
            )
            lines.discount = 0
            self._set_reward_discount_for_lines(program)
        return res

    def _get_applied_programs_with_rewards_on_current_order(self):
        """
        Override method to ignore discount in line programs by context
        """
        programs = super()._get_applied_programs_with_rewards_on_current_order()
        if self.env.context.get("ignore_reward_type_with_discount_line"):
            programs = programs.filtered(
                lambda program: program.reward_type != "discount_line"
            )
        return programs
