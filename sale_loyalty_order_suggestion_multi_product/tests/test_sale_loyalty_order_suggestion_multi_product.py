# Copyright 2024 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import Form, TransactionCase


class TestSaleLoyaltyOrderSuggestion(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_obj = cls.env["product.product"]
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test pricelist",
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "applied_on": "3_global",
                            "compute_price": "formula",
                            "base": "list_price",
                        },
                    )
                ],
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Mr. Odoo", "property_product_pricelist": cls.pricelist.id}
        )
        cls.product_a = product_obj.create({"name": "Product A", "list_price": 50})
        cls.product_b = product_obj.create({"name": "Product B", "list_price": 10})
        cls.product_c = product_obj.create({"name": "Product C", "list_price": 70})
        cls.loyalty_program = cls.env["loyalty.program"].create(
            {
                "name": "Test Sale Loyalty Order Suggestion Multi Product",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_point_mode": "order",
                            "loyalty_criteria": "multi_product",
                            "loyalty_criteria_ids": [
                                (
                                    0,
                                    0,
                                    {
                                        "product_ids": [(4, cls.product_a.id)],
                                    },
                                ),
                                (
                                    0,
                                    0,
                                    {
                                        "product_ids": [
                                            (4, cls.product_b.id),
                                            (4, cls.product_c.id),
                                        ],
                                    },
                                ),
                            ],
                        },
                    ),
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "discount",
                            "required_points": 1,
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_a
            line_form.product_uom_qty = 1
        cls.sale = sale_form.save()

    def _open_suggested_promotion_wizard(self, suggested_reward_ids):
        self.sale._update_programs_and_rewards()
        wizard = (
            self.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=self.sale)
            .create({"order_id": self.sale.id})
        )
        wizard.reward_ids = suggested_reward_ids
        return wizard

    def test_01_suggested_promotion_for_product_a_no_applicable(self):
        # In this test a suggestion is made for a promotion that contains in its rules
        # multi criteria the product added to the lines of the order but does not meet all the
        # requirements to be applied so it will be necessary to configure the
        # products in the wizard.
        line_a = self.sale.order_line.filtered(lambda x: x.product_id == self.product_a)
        wizard = self._open_suggested_promotion_wizard(line_a.suggested_reward_ids)
        self.assertEqual(wizard.reward_ids, line_a.suggested_promotion_ids.reward_ids)
        # Select promotion to apply
        wizard.selected_reward_id = self.loyalty_program.reward_ids[0].id
        # The promotion is not directly applicable as it does not comply with all the rules.
        self.assertFalse(wizard.applicable_program)
        # The wizard contains 3 lines, one for each product configured in the rules
        self.assertEqual(len(wizard.loyalty_rule_line_ids), 3)
        wiz_line_a = wizard.loyalty_rule_line_ids.filtered(
            lambda x: x.product_id == self.product_a
        )
        self.assertTrue(wiz_line_a)
        self.assertEqual(wiz_line_a.units_included, 1)
        self.assertEqual(wiz_line_a.units_required, 1)
        self.assertEqual(wiz_line_a.units_to_include, 0)
        wiz_line_b = wizard.loyalty_rule_line_ids.filtered(
            lambda x: x.product_id == self.product_b
        )
        self.assertTrue(wiz_line_b)
        self.assertEqual(wiz_line_b.units_included, 0)
        self.assertEqual(wiz_line_b.units_required, 1)
        self.assertEqual(wiz_line_b.units_to_include, 0)
        wiz_line_c = wizard.loyalty_rule_line_ids.filtered(
            lambda x: x.product_id == self.product_c
        )
        self.assertTrue(wiz_line_c)
        self.assertEqual(wiz_line_c.units_included, 0)
        self.assertEqual(wiz_line_c.units_required, 1)
        self.assertEqual(wiz_line_c.units_to_include, 0)
        # More units are added to make the promotion compliant and applicable.
        wiz_line_b.units_to_include = 1
        wiz_line_c.units_to_include = 1
        wizard.action_apply()
        line_b = self.sale.order_line.filtered(lambda x: x.product_id == self.product_b)
        self.assertTrue(line_b)
        self.assertEqual(line_b.product_uom_qty, 1)
        self.assertTrue(self.sale.order_line.filtered(lambda x: x.is_reward_line))
        line_c = self.sale.order_line.filtered(lambda x: x.product_id == self.product_c)
        self.assertTrue(line_c)
        self.assertEqual(line_c.product_uom_qty, 1)
        self.assertTrue(self.sale.order_line.filtered(lambda x: x.is_reward_line))

    def test_02_suggested_promotion_for_product_a_auto_applicable(self):
        # In this test a suggestion is made for a promotion that contains in its rules
        # the product added to the order lines and that meets all the requirements to be
        # applied.
        order_lines_values = [
            {
                "order_id": self.sale.id,
                "product_id": self.product_b.id,
                "product_uom_qty": 1.0,
            },
            {
                "order_id": self.sale.id,
                "product_id": self.product_c.id,
                "product_uom_qty": 1.0,
            },
        ]
        self.env["sale.order.line"].create(order_lines_values)
        line_a = self.sale.order_line.filtered(lambda x: x.product_id == self.product_a)
        wizard = self._open_suggested_promotion_wizard(line_a.suggested_reward_ids)
        self.assertEqual(wizard.reward_ids, line_a.suggested_promotion_ids.reward_ids)
        # Select promotion to apply
        wizard.selected_reward_id = self.loyalty_program.reward_ids[0].id
        # The promotion is directly applicable as it does not comply with all the rules.
        self.assertTrue(wizard.applicable_program)
        # The wizard contains 0 lines
        self.assertEqual(len(wizard.loyalty_rule_line_ids), 0)
        self.assertTrue(self.sale.order_line.filtered(lambda x: not x.is_reward_line))
        wizard.action_apply()
        self.assertTrue(self.sale.order_line.filtered(lambda x: x.is_reward_line))
