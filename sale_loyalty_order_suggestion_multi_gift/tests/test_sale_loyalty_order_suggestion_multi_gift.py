# Copyright 2024 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import Form, TransactionCase


class TestSaleLoyaltyOrderSuggestion(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
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
        cls.product_1 = cls.env["product.product"].create(
            {"name": "Test 1", "sale_ok": True, "list_price": 50}
        )
        cls.product_2 = cls.env["product.product"].create(
            {"name": "Test 2", "sale_ok": False, "list_price": 60}
        )
        cls.product_3 = cls.env["product.product"].create(
            {"name": "Test 3", "sale_ok": False, "list_price": 70}
        )
        cls.product_4 = cls.env["product.product"].create(
            {"name": "Test 4", "sale_ok": False, "list_price": 80}
        )
        cls.loyalty_program_form = cls.env["loyalty.program"].create(
            {
                "name": "Test Multi Gift Program",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 2,
                            "minimum_amount": 0,
                        },
                    ),
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "multi_gift",
                            "required_points": 1,
                            "loyalty_multi_gift_ids": [
                                (
                                    0,
                                    0,
                                    {
                                        "reward_product_ids": [(4, cls.product_2.id)],
                                        "reward_product_quantity": 2,
                                    },
                                ),
                                (
                                    0,
                                    0,
                                    {
                                        "reward_product_ids": [
                                            (4, cls.product_3.id),
                                            (4, cls.product_4.id),
                                        ],
                                        "reward_product_quantity": 3,
                                    },
                                ),
                            ],
                        },
                    )
                ],
            }
        )
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_1
            line_form.product_uom_qty = 1
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_2
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

    def test_01_suggested_promotion_for_product_no_applicable(self):
        # In this test a suggestion is made for a promotion which contains in its rewards
        # multi-gift product added to the order lines but does not meet all of the
        # requirements to be applied so it will be necessary to configure the products in the
        # products in the wizard.
        self.sale.order_line.filtered(lambda x: x.product_id == self.product_1).unlink()
        line_2 = self.sale.order_line.filtered(lambda x: x.product_id == self.product_2)
        wizard = self._open_suggested_promotion_wizard(line_2.suggested_reward_ids)
        self.assertEqual(wizard.reward_ids, line_2.suggested_promotion_ids.reward_ids)
        self.assertTrue(
            self.loyalty_program_form in line_2.suggested_reward_ids.program_id
        )
        # Select promotion to apply
        wizard.selected_reward_id = self.loyalty_program_form.reward_ids[0].id
        # The promotion is not directly applicable as it does not comply with all the rules.
        self.assertFalse(wizard.applicable_program)
        # The wizard contains all the products to add as no specific product has been
        # set but among these products is the product added to the order lines and this
        # is the one we will proceed with the test.
        self.assertTrue(len(wizard.loyalty_rule_line_ids) > 0)
        wiz_line_2 = wizard.loyalty_rule_line_ids.filtered(
            lambda x: x.product_id == self.product_2
        )
        self.assertEqual(wiz_line_2.units_included, 1)
        self.assertEqual(wiz_line_2.units_required, 2)
        self.assertEqual(wiz_line_2.units_to_include, 0)
        # More units are added to make the promotion compliant and applicable.
        # If more quantity of the reward product is added from the wizard to apply the
        # promotion, it is considered that more quantity of product is wanted in addition
        # to the reward so the initial quantity added to the sales order will be respected.
        wiz_line_2.units_to_include = 1
        wizard.action_apply()
        self.assertEqual(
            self.sale.order_line.filtered(
                lambda x: x.product_id == self.product_2 and not x.is_reward_line
            ).product_uom_qty,
            2,
        )
        self.assertEqual(
            self.sale.order_line.filtered(
                lambda x: x.product_id == self.product_2 and x.is_reward_line
            ).product_uom_qty,
            2,
        )
        self.assertEqual(
            self.sale.order_line.filtered(
                lambda x: x.product_id == self.product_3 and x.is_reward_line
            ).product_uom_qty,
            3,
        )
        self.assertFalse(
            self.sale.order_line.filtered(
                lambda x: x.product_id == self.product_4 and x.is_reward_line
            )
        )

    def test_02_no_suggested_promotion_for_product_1(self):
        # This test checks that the promotion containing reward products is not found
        # in the suggested promotions as product_1 is not part of the rewards.
        self.loyalty_program_form.rule_ids.minimum_amount = 200
        self.loyalty_program_form.rule_ids.minimum_qty = 0
        line_1 = self.sale.order_line.filtered(lambda x: x.product_id == self.product_1)
        self.assertFalse(
            self.loyalty_program_form in line_1.suggested_reward_ids.program_id
        )
