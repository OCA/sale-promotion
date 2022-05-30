from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_applicable_no_code_promo_program(self):
        """
        Override method for return programs other than fixed price reward type
        """
        self.ensure_one()
        return (
            super()
            ._get_applicable_no_code_promo_program()
            .filtered(
                lambda program: program.reward_type != "fixed_price",
            )
        )

    def _get_applicable_no_code_promo_fixed_price_program(self):
        """
        Return actual programs with reward type is fixed price
        """
        self.ensure_one()
        programs = (
            self.env["coupon.program"]
            .with_context(
                no_outdated_coupons=True,
                applicable_coupon=True,
            )
            .search(
                [
                    "&",
                    ("reward_type", "=", "fixed_price"),
                    ("promo_code_usage", "=", "no_code_needed"),
                    "|",
                    ("rule_date_from", "=", False),
                    ("rule_date_from", "<=", self.date_order),
                    "|",
                    ("rule_date_to", "=", False),
                    ("rule_date_to", ">=", self.date_order),
                    "|",
                    ("company_id", "=", self.company_id.id),
                    ("company_id", "=", False),
                ]
            )
            ._filter_programs_from_common_rules(self)
        )
        return programs

    def _create_new_no_code_promo_reward_lines(self):
        """
        Override core method to save program with new reward rule
        """
        self.ensure_one()
        super()._create_new_no_code_promo_reward_lines()
        order = self
        programs = order._get_applicable_no_code_promo_fixed_price_program()
        programs = (
            programs._keep_only_most_interesting_auto_applied_global_discount_program()
        )
        for program in programs:
            error_status = program._check_promo_code(order, False)
            if not error_status.get("error"):
                order.no_code_promo_program_ids |= program
        else:
            super()._create_new_no_code_promo_reward_lines()

    def _set_reward_fixed_price_for_lines(self, program):
        """
        Update discount field by program
        """
        price_unit = program.price_unit
        lines = self._get_paid_order_lines()
        if program.discount_apply_on == "cheapest_product":
            line = self._get_cheapest_line()
            if line:
                line.price_unit = price_unit
        elif program.discount_apply_on in ["specific_products", "on_order"]:
            if program.discount_apply_on == "specific_products":
                # We should not exclude reward line that offer this product
                # since we need to offer only the discount on
                # the real paid product (regular product - free product)
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
            for line in lines:
                line.price_unit = price_unit
        elif program.discount_apply_on == "domain_product":
            # for compatibility with `sale_promotion_domain_product_discount` module
            lines = (self.order_line - self._get_reward_lines()).filtered(
                lambda line: program._get_valid_products(line.product_id),
            )
            for line in lines:
                line.price_unit = price_unit

    def _get_reward_line_values(self, program):
        """
        Overrider core method to set fixed price for line if program has
        'fixed_price' reward type
        """
        if program.reward_type == "fixed_price":
            self._set_reward_fixed_price_for_lines(program)
            return []
        else:
            return super()._get_reward_line_values(program)

    def _update_existing_reward_lines(self):
        """
        Override method to add context to ignore programs with reward type is fixed_price
        and update price of lines
        """
        self.ensure_one()
        res = super(
            SaleOrder,
            self.with_context(ignore_reward_type_with_fixed_price_line=True),
        )._update_existing_reward_lines()
        order = self
        applied_fixed_price_programs = (
            order._get_applied_programs_with_rewards_on_current_order().filtered(
                lambda program: program.reward_type == "fixed_price",
            )
        )
        for program in applied_fixed_price_programs:
            self._set_reward_fixed_price_for_lines(program)
        return res

    def _get_applied_programs_with_rewards_on_current_order(self):
        """
        Override method to ignore programs with fixed price by context
        """
        programs = super()._get_applied_programs_with_rewards_on_current_order()
        if self.env.context.get("ignore_reward_type_with_fixed_price_line"):
            programs = programs.filtered(
                lambda program: program.reward_type != "fixed_price"
            )
        return programs
