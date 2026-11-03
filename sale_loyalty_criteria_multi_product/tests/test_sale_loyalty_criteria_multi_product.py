# Copyright 2021 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form

from odoo.addons.loyalty_criteria_multi_product.tests import (
    test_loyalty_criteria_multi_product,
)


class TestSaleLoyaltyCriteriaMultiProduct(
    test_loyalty_criteria_multi_product.TestLoyaltyCriteriaMultiProduct
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.whiteboard_pen = cls.env["product.product"].create(
            {
                "name": "Whiteboard Pen",
                "list_price": 1.20,
            }
        )
        cls.reward = cls.env["loyalty.reward"].create(
            {
                "program_id": cls.loyalty_program.id,
                "reward_type": "product",
                "reward_product_id": cls.whiteboard_pen.id,
                "reward_product_qty": 1,
                "required_points": 1,
            }
        )

        # Create sale order that meets the criteria:
        # - Product A (required by first criteria)
        # - Product B and C (required by second criteria)
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_a
            line_form.product_uom_qty = 1
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_b
            line_form.product_uom_qty = 1
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_c
            line_form.product_uom_qty = 1
        cls.sale = sale_form.save()

    def _check_program_applicable(self, sale, program, should_be_applicable=True):
        """Helper method to check if a program is applicable to a sale order"""
        # Update programs to check if they meet criteria
        sale._update_programs_and_rewards()

        # Get programs as recordset
        programs = self.env["loyalty.program"].browse([program.id])

        # Check if the program should be applicable
        program_results = sale._program_check_compute_points(programs)
        program_result = program_results.get(program, {})

        if should_be_applicable:
            self.assertFalse(
                program_result.get("error", False),
                f"Program should be applicable but got error: "
                f"{program_result.get('error', '')}",
            )
        else:
            self.assertTrue(
                program_result.get("error", False),
                "Program should not be applicable but no error was found",
            )
            self.assertIn(
                "required product quantities", program_result.get("error", "")
            )

    def test_01_sales_order_meets_the_criteria(self):
        """When all the criterias are matched we can apply the program"""
        # The sale order has Product A, B, and C which meets all criteria
        self._check_program_applicable(
            self.sale, self.loyalty_program, should_be_applicable=True
        )

    def test_02_sales_order_no_meets_the_criteria(self):
        """ "When all the criteria do not match, we cannot apply the program.
        At least one of the rules must be fulfilled"."""
        # Remove product_c to break the second criteria (needs both B and C)
        self.sale.order_line.filtered(lambda x: x.product_id == self.product_c).unlink()

        # Should not be applicable now
        self._check_program_applicable(
            self.sale, self.loyalty_program, should_be_applicable=False
        )

        # Change product_b to product_c - this still meets the second criteria
        # since it has both B and C products (line_b becomes C, and we still -
        # have the original C)
        line_b = self.sale.order_line.filtered(lambda x: x.product_id == self.product_b)
        line_b.product_id = self.product_c

        # Add product_b back to meet the criteria
        with Form(self.sale) as sale_form:
            with sale_form.order_line.new() as line_form:
                line_form.product_id = self.product_b
                line_form.product_uom_qty = 1

        self._check_program_applicable(
            self.sale, self.loyalty_program, should_be_applicable=True
        )

    def test_03_loyalty_criteria_ids_list_empty(self):
        """When a rule is set as multi-product but the list of criteria is left empty,
        the promotion will be applicable in any case as there are no criteria and the
        rule does not restrict."""
        self.loyalty_program.rule_ids.loyalty_criteria_ids = [(5, 0, 0)]

        self._check_program_applicable(
            self.sale, self.loyalty_program, should_be_applicable=True
        )

    def test_04_not_all_rules_have_defined_criteria(self):
        """When not all rules have defined criteria, then the criteria will
        have no effect on the application of the program, only a program with
         defined criteria in all its rules will be able to
         restrict the application of the program."""
        self.loyalty_program.rule_ids[0].loyalty_criteria = "domain"
        self.sale.order_line.filtered(lambda x: x.product_id == self.product_c).unlink()

        # Should still be applicable since the rule no longer has multi_product criteria
        self._check_program_applicable(
            self.sale, self.loyalty_program, should_be_applicable=True
        )
