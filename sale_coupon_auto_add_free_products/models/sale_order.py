# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _is_reward_in_order_lines(self, program):
        # Let's add missing products while checking code rewards,
        # that way we don't need to change the promo/coupon code checking code
        is_reward_in = super()._is_reward_in_order_lines(program)

        if not is_reward_in and program.auto_add_free_products:
            return self._add_missing_product_quantities(program)

        return is_reward_in

    def _add_missing_product_quantities(self, program):
        # Compute and add missing products for this program
        reward_products_order_lines = self.order_line.filtered(
            lambda line: line.product_id == program.reward_product_id
        )
        reward_product_quantity = sum(
            reward_products_order_lines.mapped("product_uom_qty")
        )

        valid_product_order_lines = (
            self.order_line - self._get_reward_lines()
        ).filtered(lambda x: program._get_valid_products(x.product_id))
        valid_quantity = sum(valid_product_order_lines.mapped("product_uom_qty"))

        if (
            not program.always_reward_product
            and valid_quantity < program.rule_min_quantity
        ):
            # We need to be at least at min quantity
            # Even if the program includes itself it would mean buying one
            # more product to get reward_product_quantity free products
            return False

        # Missing quantity is current rewarded product quantity to total reward product quantity
        missing_quantity = program.reward_product_quantity - reward_product_quantity

        # If the program apply to itself
        if (
            not program.always_reward_product
            and program._get_valid_products(program.reward_product_id)
            and reward_product_quantity == valid_quantity
        ):
            # If there's only the rewarded product as valid
            # We need to reach min + reward:
            # buy 2 get 3 free is implemented with min = 2 reward = 3
            # so we need 5 products in total
            missing_quantity += program.rule_min_quantity

        if missing_quantity <= 0:
            # We don't need to add product, no reward here
            return False

        if reward_products_order_lines:
            # If products are already there but non in sufficient quantity
            # Add missing quantity to last product:
            reward_products_order_line = reward_products_order_lines[-1]
            reward_products_order_line.product_uom_qty += missing_quantity
            reward_products_order_line.auto_added_for_program_id = program.id
            reward_products_order_line.auto_added_qty = missing_quantity
        else:
            # We need to add this product in corresponding quantity
            self._add_missing_product(
                program.reward_product_id, missing_quantity, program
            )

        return True

    def _add_missing_product(self, product, quantity, program):
        # Add a sale order line for the product with the quantity
        self.ensure_one()
        self.write(
            {
                "order_line": [
                    (
                        0,
                        False,
                        {
                            "product_id": product.id,
                            "product_uom_qty": quantity,
                            "auto_added_for_program_id": program.id,
                            "auto_added_qty": quantity,
                        },
                    )
                ]
            }
        )

    def recompute_coupon_lines(self):
        # Add missing products before computing promotions
        self._auto_add_eligible_products()
        super().recompute_coupon_lines()

    def _get_applicable_programs(self):
        # We need to also return programs that could become applicable after
        # free products addition
        return (
            super()._get_applicable_programs()
            | self._get_maybe_applicable_programs_with_auto_add()
        )

    def _get_maybe_applicable_programs_with_auto_add(self, no_code=False):
        # Find all non applicable programs that could become applicable with
        # product auto addition
        maybe_applicable_domain = [
            ("auto_add_free_products", "=", True),
            ("promo_applicability", "=", "on_current_order"),
            ("reward_type", "=", "product"),
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
        if no_code:
            maybe_applicable_domain.append(("promo_code_usage", "=", "no_code_needed"))

        programs = self.env["coupon.program"].search(maybe_applicable_domain)
        programs = programs and programs._filter_on_mimimum_amount(self)
        programs = programs and programs._filter_on_validity_dates(self)
        programs = programs and programs._filter_unexpired_programs(self)
        programs = programs and programs._filter_programs_on_partners(self)
        if not no_code:
            programs = programs and programs._filter_programs_on_products(self)

        return programs

    def _auto_add_eligible_products(self):
        # Find programs with free products and auto add flags
        order = self
        order_lines = (
            order.order_line.filtered(lambda line: line.product_id)
            - order._get_reward_lines()
        )
        products = order_lines.mapped("product_id")

        programs = order._get_maybe_applicable_programs_with_auto_add(no_code=True)
        for program in programs:
            if not program.always_reward_product and not program._get_valid_products(
                products
            ):
                continue

            self._add_missing_product_quantities(program)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    auto_added_qty = fields.Float(
        string="Auto Added Quantity", digits="Product Unit of Measure"
    )
    auto_added_for_program_id = fields.Many2one("coupon.program", copy=False)

    def unlink(self):
        lines_to_remove = self.env["sale.order.line"]
        for order_line in self:
            if not order_line.is_reward_line:
                continue
            program = self.env["coupon.program"].search(
                [("discount_line_product_id", "=", order_line.product_id.id)]
            )
            if not program or program.reward_type != "product":
                continue
            product_line = order_line.order_id.order_line.filtered(
                lambda sol: sol.auto_added_for_program_id == program
            )
            product_line.product_uom_qty = max(
                0, product_line.product_uom_qty - product_line.auto_added_qty
            )
            if product_line.product_uom_qty == 0:
                lines_to_remove |= product_line

        # Add all lines to be removed to the current recordset
        self |= lines_to_remove
        # And unlink all (this prevents ui error in odoo)
        return super().unlink()
