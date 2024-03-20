# Copyright 2021 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
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
        # We'll be using this sale order
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

    def _action_apply_program(self, sale, program):
        sale._update_programs_and_rewards()
        wizard = (
            self.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=sale)
            .create({"selected_reward_id": program.reward_ids.id})
        )
        wizard.action_apply()

    def test_01_sales_order_meets_the_criteria(self):
        """When all the criterias are matched we can apply the program"""
        # The discount is correctly applied
        self._action_apply_program(self.sale, self.loyalty_program)
        self.assertTrue(bool(self.sale.order_line.filtered("is_reward_line")))

    def test_02_sales_order_no_meets_the_criteria(self):
        """ "When all the criteria do not match, we cannot apply the program. At least one
        of the rules must be fulfilled"."""
        self.sale.order_line.filtered(lambda x: x.product_id == self.product_c).unlink()
        with self.assertRaises(ValidationError):
            self._action_apply_program(self.sale, self.loyalty_program)
        self.assertFalse(bool(self.sale.order_line.filtered("is_reward_line")))
        # Change product_b to product_c to meet the criterion of at least one rule
        line_b = self.sale.order_line.filtered(lambda x: x.product_id == self.product_b)
        line_b.product_id = self.product_c
        self._action_apply_program(self.sale, self.loyalty_program)
        self.assertTrue(bool(self.sale.order_line.filtered("is_reward_line")))

    def test_03_loyalty_criteria_ids_list_empty(self):
        """When a rule is set as multi-product but the list of criteria is left empty,
        the promotion will be applicable in any case as there are no criteria and the
        rule does not restrict."""
        self.loyalty_program.rule_ids.loyalty_criteria_ids = []
        self._action_apply_program(self.sale, self.loyalty_program)
        self.assertTrue(bool(self.sale.order_line.filtered("is_reward_line")))

    def test_04_not_all_rules_have_defined_criteria(self):
        """When not all rules have defined criteria, then the criteria will have no effect
        on the application of the program, only a program with defined criteria in all its
        rules will be able to restrict the application of the program."""
        self.loyalty_program.rule_ids[0].loyalty_criteria = "domain"
        self.sale.order_line.filtered(lambda x: x.product_id == self.product_c).unlink()
        self._action_apply_program(self.sale, self.loyalty_program)
        self.assertTrue(bool(self.sale.order_line.filtered("is_reward_line")))
