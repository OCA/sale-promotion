from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_program_reward_lines_to_set_delivered_reward_qty(self, program):
        return self.order_line.filtered(
            lambda line: line.product_id == program.discount_line_product_id
        )

    def _set_delivered_reward_qty_for_program_product(self, program):
        # In case of free product reward should be delivered only if the
        # free product is delivered
        product_line = self.order_line.filtered(
            lambda sol: sol.product_id == program.reward_product_id
        )
        reward_lines = self._get_program_reward_lines_to_set_delivered_reward_qty(
            program
        )
        reward_lines.write(
            {"delivered_reward_qty": 1 if product_line.qty_delivered > 0 else 0}
        )

    def _set_delivered_reward_qty_for_program_discount_fixed_amount(self, program):
        reward_lines = self._get_program_reward_lines_to_set_delivered_reward_qty(
            program
        )
        # In case of fixed amount for now let's consider it delivered
        reward_lines.write({"delivered_reward_qty": 1})

    def _set_delivered_reward_qty_for_program_discount_percentage_cheapest_product(
        self, program
    ):
        reward_lines = self._get_program_reward_lines_to_set_delivered_reward_qty(
            program
        )
        line = self._get_cheapest_line()
        reward_lines.write({"delivered_reward_qty": 1 if line.qty_delivered > 0 else 0})

    def _set_delivered_reward_qty_for_program_discount_percentage_specific_products(
        self, program
    ):
        lines = self._get_paid_order_lines()
        # We should not exclude reward line that offer this
        # product since we need to offer only the discount
        # on the real paid product
        # (regular product - free product)
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
        self._set_delivered_reward_qty_for_program_discount_percentage_on_specific_lines(
            program, lines
        )

    def _set_delivered_reward_qty_for_program_discount_percentage_on_order(
        self, program
    ):
        lines = self._get_paid_order_lines()
        self._set_delivered_reward_qty_for_program_discount_percentage_on_specific_lines(
            program, lines
        )

    def _set_delivered_reward_qty_for_program_discount_percentage_on_specific_lines(
        self, program, lines
    ):
        reward_lines = self._get_program_reward_lines_to_set_delivered_reward_qty(
            program
        )
        amount_total = sum(
            [
                any(line.tax_id.mapped("price_include"))
                and line.price_total
                or line.price_subtotal
                for line in self._get_base_order_lines(program)
            ]
        )

        discount_by_taxes = {}
        currently_discounted_amount = 0
        for line in lines:
            discount_line_amount = min(
                line.qty_delivered
                * line.price_reduce
                * (program.discount_percentage / 100),
                amount_total - currently_discounted_amount,
            )

            if discount_line_amount:
                if line.tax_id in discount_by_taxes:
                    discount_by_taxes[line.tax_id] -= discount_line_amount
                else:
                    discount_by_taxes[line.tax_id] = (
                        -discount_line_amount if discount_line_amount > 0 else 0
                    )

            currently_discounted_amount += discount_line_amount

        for line in reward_lines:
            line.write(
                {
                    "delivered_reward_qty": discount_by_taxes.get(line.tax_id, 0)
                    / line.price_unit
                }
            )

    def _set_delivered_reward_qty_for_program_discount_percentage(self, program):
        if program.discount_apply_on == "cheapest_product":
            self._set_delivered_reward_qty_for_program_discount_percentage_cheapest_product(
                program
            )
        elif program.discount_apply_on == "specific_products":
            self._set_delivered_reward_qty_for_program_discount_percentage_specific_products(
                program
            )
        elif program.discount_apply_on == "on_order":
            self._set_delivered_reward_qty_for_program_discount_percentage_on_order(
                program
            )

    def _set_delivered_reward_qty_for_program_discount(self, program):
        if program.discount_type == "fixed_amount":
            self._set_delivered_reward_qty_for_program_discount_fixed_amount(program)
        elif program.discount_type == "percentage":
            self._set_delivered_reward_qty_for_program_discount_percentage(program)

    def _set_delivered_reward_qty_for_program(self, program):
        if program.reward_type == "product":
            self._set_delivered_reward_qty_for_program_product(program)
        elif program.reward_type == "discount":
            self._set_delivered_reward_qty_for_program_discount(program)

    def recompute_coupon_lines(self):
        super().recompute_coupon_lines()
        self._update_delivered_coupon_lines_quantity()

    def _update_delivered_coupon_lines_quantity(self):
        applied_programs = self._get_applied_programs_with_rewards_on_current_order()
        order_lines = (
            self.order_line.filtered(lambda line: line.product_id)
            - self._get_reward_lines()
        )
        products = order_lines.mapped("product_id")

        for program in applied_programs:

            # First check if program still applies on delivered quantities

            # To keep it simple for now only check if at least one of
            # necessary products is delivered

            valid_products = (
                (
                    program._get_valid_products(products)
                    if program.rule_products_domain
                    and program.rule_products_domain != "[]"
                    else products
                )
                if program.reward_type != "product"
                else program.reward_product_id
            )
            qty_delivered = sum(
                order_lines.filtered(
                    lambda sol: sol.product_id in valid_products
                ).mapped("qty_delivered")
            )
            if not qty_delivered:
                reward_lines = (
                    self._get_program_reward_lines_to_set_delivered_reward_qty(program)
                )
                reward_lines.write({"delivered_reward_qty": 0})
                continue

            # Do we consider reward for rule_minimum_amount delivered only when
            # this minimum amount has been delivered?

            self._set_delivered_reward_qty_for_program(program)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    qty_delivered_method = fields.Selection(
        selection_add=[("reward_stock_move", "Reward from Stock Moves")]
    )
    delivered_reward_qty = fields.Float(
        string="Prorata of reward from delivered quantities",
        digits=0,
    )

    @api.depends("is_reward_line")
    def _compute_qty_delivered_method(self):
        super(SaleOrderLine, self)._compute_qty_delivered_method()

        for line in self:
            if line.is_reward_line:
                line.qty_delivered_method = "reward_stock_move"

    @api.depends("delivered_reward_qty")
    def _compute_qty_delivered(self):
        # Might be interesting to directly compute delivered quantities here instead
        super(SaleOrderLine, self)._compute_qty_delivered()

        for line in self:
            if line.qty_delivered_method == "reward_stock_move":
                line.qty_delivered = line.delivered_reward_qty

    @api.onchange("product_uom_qty")
    def _onchange_product_uom_qty(self):
        rv = super()._onchange_product_uom_qty()

        if (
            self.state == "sale"
            and self.product_id.type in ["product", "consu"]
            and self.order_id.order_line.filtered(
                lambda sol: sol.is_reward_line and sol.qty_invoiced > 0
            )
        ):
            warning_mess = {
                "title": _("Ordered quantity changed on already invoiced order!"),
                "message": _(
                    "You are changing the ordered quantity on an already "
                    "invoiced order with partial promotion delivered! "
                    "This could result on inconsistencies on promotion amount "
                    "for future invoices. Beware!"
                ),
            }
            return {"warning": warning_mess}

        return rv
