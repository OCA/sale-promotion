# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    processed_programs_ids = fields.Many2many("coupon.program", store=False, copy=False)
    active_programs_ids = fields.Many2many("coupon.program", store=False, copy=False)
    original_paid_order_lines = fields.Boolean(
        "Chainable Techincal Field", store=False, copy=False
    )

    def _update_existing_reward_lines(self):
        # We need to store the already processed programs to take their discount
        # in account in the further discount

        # Ensure we start the computation with no already processed programs
        self.processed_programs_ids -= self.processed_programs_ids
        rv = super()._update_existing_reward_lines()
        # Leave these many2many empty
        self.active_programs_ids -= self.active_programs_ids
        self.processed_programs_ids -= self.processed_programs_ids
        return rv

    def _add_active_program_discount_lines(self, paid_order_lines):
        for program in self.active_programs_ids:
            paid_order_lines |= self.order_line.filtered(
                lambda line: line.product_id == program.discount_line_product_id
            )
        return paid_order_lines

    def _get_paid_order_lines(self):
        # We return product order lines and previous discounts in case of
        # a chainable promotion
        paid_order_lines = super()._get_paid_order_lines()
        if self.original_paid_order_lines:
            return paid_order_lines
        return self._add_active_program_discount_lines(paid_order_lines)

    def _get_reward_values_discount(self, program):
        # Start by filtering out chained programs that have a chained minimum
        # amount not reached
        if (
            program.rule_minimum_amount_chained
            and program.rule_minimum_amount
            and program.discount_type == "percentage"
            and program.promo_applicability == "on_current_order"
            and program.chainable
        ):
            no_effect_lines = self._get_no_effect_on_threshold_lines()
            order_amount = {
                "amount_untaxed": self.amount_untaxed
                - sum(line.price_subtotal for line in no_effect_lines),
                "amount_tax": self.amount_tax
                - sum(line.price_tax for line in no_effect_lines),
            }
            if program.reward_type != "discount":
                # avoid the filtered
                lines = self.env["sale.order.line"]
            else:
                lines = self.order_line.filtered(
                    lambda line: line.product_id == program.discount_line_product_id
                    or line.product_id == program.reward_id.discount_line_product_id
                )
            untaxed_amount = order_amount["amount_untaxed"] - sum(
                line.price_subtotal for line in lines
            )
            tax_amount = order_amount["amount_tax"] - sum(
                line.price_tax for line in lines
            )
            program_amount = program._compute_program_amount(
                "rule_minimum_amount", self.currency_id
            )
            if not (
                program.rule_minimum_amount_tax_inclusion == "tax_included"
                and program_amount <= (untaxed_amount + tax_amount)
                or program_amount <= untaxed_amount
            ):
                # We need to explicitly remove the program from the active programs
                # since it has not been taken in account at the initial filter
                self.no_code_promo_program_ids -= program
                self.code_promo_program_id -= program
                return []

        # We set active_programs_ids to processed_programs_ids
        # if we need to take these in account

        # If the current program is a chainable discount then take
        # other percentage program discounts in account to compute
        # the final discount

        if (
            program.discount_type == "percentage"
            and program.promo_applicability == "on_current_order"
            and program.chainable
        ):
            self.active_programs_ids = self.processed_programs_ids
        else:
            self.active_programs_ids -= self.active_programs_ids

        # If the program apply on specific products be sure to add discount
        # products for the discount to be added in the computation
        if (
            program.discount_apply_on == "specific_products"
            and self.active_programs_ids
        ):
            old_discount_specific_product_ids = program.discount_specific_product_ids
            for active_program in self.active_programs_ids:
                program.discount_specific_product_ids += (
                    active_program.discount_line_product_id
                )

        reward_values_discount = super()._get_reward_values_discount(program)

        # Filter empty promotion (promotion on only a promotion for instance)
        reward_values_discount = [
            vals for vals in reward_values_discount if vals["price_unit"]
        ]

        # Restore the specific products to their original value
        if (
            program.discount_apply_on == "specific_products"
            and self.active_programs_ids
        ):
            program.discount_specific_product_ids = old_discount_specific_product_ids

        # Keep all already processed programs for them to be taken in account
        # in further chainable programs computation
        self.processed_programs_ids += program

        return reward_values_discount

    def _get_applied_programs_with_rewards_on_current_order(self):
        # Programs need to be sorted on their sequences
        applied_programs = super()._get_applied_programs_with_rewards_on_current_order()
        # We take the default order here in order to be coherent with the UI
        return applied_programs.sorted()

    def _filter_lines_rewarded_for_program_on_specific_products(self, lines, program):
        # We need to filter out the lines that are not on the same
        # specific products as the current program
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
                    ]
                )
                .mapped("discount_line_product_id")
            )
            lines = lines.filtered(
                lambda x: x.product_id
                in (program.discount_specific_product_ids | free_product_lines)
            )

        return lines

    def _get_reward_values_discount_from_specific_products_program(
        self, program, original_program, line
    ):
        # Compute the original_program discount on program specific_products
        # We can't call super here due to sale_coupon_delivery being a bad citizen
        self.original_paid_order_lines = True
        lines = self._get_paid_order_lines()
        self.original_paid_order_lines = False

        # First filter out lines with different taxes than the current line
        lines = lines.filtered(lambda x: x.tax_id == line.tax_id)

        # Then if the orginal_program is also on specific products, we need to
        # remove the other lines
        lines = self._filter_lines_rewarded_for_program_on_specific_products(
            lines, original_program
        )

        # Then remove the current program other lines too
        lines = self._filter_lines_rewarded_for_program_on_specific_products(
            lines, program
        )

        # Finally apply the same computation as in sale_coupon.sale_order
        amount_total = sum(
            self._get_base_order_lines(original_program).mapped("price_subtotal")
        )
        currently_discounted_amount = 0
        discount = 0
        for line in lines:
            discount_line_amount = min(
                super()._get_reward_values_discount_percentage_per_line(
                    original_program, line
                ),
                amount_total - currently_discounted_amount,
            )
            discount -= discount_line_amount
            currently_discounted_amount += discount_line_amount

        return discount

    def _get_reward_values_discount_percentage_per_line(self, program, line):
        if (
            not line.is_reward_line
            or program.discount_apply_on in ["on_order", "cheapest_product"]
            or not self.active_programs_ids
        ):
            return super()._get_reward_values_discount_percentage_per_line(
                program, line
            )

        # We have active_programs and this program is on specific_products
        # We need to check if this line is a reward from an active program
        original_program = self.active_programs_ids.filtered(
            lambda x: x.discount_line_product_id == line.product_id
        )
        if (
            not original_program
            or original_program.reward_type != "discount"
            or original_program.discount_type != "percentage"
        ):
            return super()._get_reward_values_discount_percentage_per_line(
                program, line
            )

        # This line price is a reward but the reward is not on these specific products
        # We need to recompute partial discount here:
        discount = self._get_reward_values_discount_from_specific_products_program(
            program, original_program, line
        )

        return line.product_uom_qty * discount * (program.discount_percentage / 100)
