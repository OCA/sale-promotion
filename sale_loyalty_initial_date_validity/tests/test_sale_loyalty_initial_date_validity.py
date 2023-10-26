# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestSaleLoyaltyInitialDateValidity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        loyalty_program = cls.env["loyalty.program"]
        # Promotion with start date currently valid
        cls.promotion1 = loyalty_program.create(
            {
                "name": "Test with start date currently valid",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "date_from": date.today() - timedelta(days=1),
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    )
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "discount",
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )
        # Promotion with a future start date
        cls.promotion2 = loyalty_program.create(
            {
                "name": "Test with a future start date",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "date_from": date.today() + timedelta(days=1),
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    )
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "discount",
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "list_price": 100}
        )

    def _action_apply_program(self, sale, program):
        sale._update_programs_and_rewards()
        wizard = (
            self.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=sale)
            .create({"selected_reward_id": program.reward_ids.id})
        )
        wizard.action_apply()

    def _create_sale(self):
        """Helper method to create sales in the test cases"""
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1
        return sale_form.save()

    def test_01_sale_loyalty_initial_date_validity(self):
        """It is verified that the promotion is applicable to a sales order that fulfils
        the conditions of the promotion. The condition is that the promotion is
        applicable from the current date."""
        sale_order = self._create_sale()
        self._action_apply_program(sale_order, self.promotion1)
        self.assertTrue(bool(sale_order.order_line.filtered("is_reward_line")))

    def test_02_sale_loyalty_initial_date_validity(self):
        """It is checked that the promotion is not applicable to a sell order that
        fulfils the conditions of the promotion. The condition is that the promotion is
        not applicable until tomorrow."""
        sale_order = self._create_sale()
        with self.assertRaises(ValidationError):
            self._action_apply_program(sale_order, self.promotion2)
        self.assertFalse(bool(sale_order.order_line.filtered("is_reward_line")))
