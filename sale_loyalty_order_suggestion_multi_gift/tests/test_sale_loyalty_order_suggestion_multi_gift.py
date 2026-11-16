# Copyright 2024 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestSaleLoyaltyOrderSuggestion(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test pricelist",
                "item_ids": [
                    Command.create(
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
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 2,
                            "minimum_amount": 0,
                        },
                    ),
                ],
                "reward_ids": [
                    Command.create(
                        {
                            "reward_type": "multi_gift",
                            "required_points": 1,
                            "loyalty_multi_gift_ids": [
                                Command.create(
                                    {
                                        "reward_product_ids": [(4, cls.product_2.id)],
                                        "reward_product_quantity": 2,
                                    },
                                ),
                                Command.create(
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
        cls.loyalty_program_same_product = cls.env["loyalty.program"].create(
            {
                "name": "Test Same Product Buy2 Get2",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 2,
                            "minimum_amount": 0,
                            "product_ids": [(4, cls.product_2.id)],
                        },
                    ),
                ],
                "reward_ids": [
                    Command.create(
                        {
                            "reward_type": "multi_gift",
                            "required_points": 1,
                            "loyalty_multi_gift_ids": [
                                Command.create(
                                    {
                                        "reward_product_ids": [
                                            (4, cls.product_2.id),
                                            (4, cls.product_4.id),
                                        ],
                                        "reward_product_quantity": 2,
                                    },
                                ),
                            ],
                        },
                    ),
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
        # In this test a suggestion is made for a promotion which contains in its
        # rewards multi-gift product added to the order lines but does not meet all of
        # the requirements to be applied so it will be necessary to configure the
        # products in the products in the wizard.
        self.sale.order_line.filtered(lambda x: x.product_id == self.product_1).unlink()
        line_2 = self.sale.order_line.filtered(lambda x: x.product_id == self.product_2)
        wizard = self._open_suggested_promotion_wizard(line_2.suggested_reward_ids)
        self.assertEqual(wizard.reward_ids, line_2.suggested_promotion_ids.reward_ids)
        self.assertTrue(
            self.loyalty_program_form in line_2.suggested_reward_ids.program_id
        )
        # Select promotion to apply
        wizard.selected_reward_id = self.loyalty_program_form.reward_ids[0].id
        # The promotion is not directly applicable as it does not comply with all the
        # rules.
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
        # promotion, it is considered that more quantity of product is wanted in
        # addition to the reward so the initial quantity added to the sales order will
        # be respected.
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

    def test_03_same_product_buy2_get2_buy2_results_in_2_paid_and_2_free(self):
        # Check that if the order complies with the rules, even if the promotion is
        # suggested, the correct quantities are applied to the order lines.
        # For example: if the rule requires 2 and rewards 2 of the same product,
        # when buying 2, 2 are paid for + 2 are rewarded.
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product_2
            line_form.product_uom_qty = 2
        sale = sale_form.save()
        sale._update_programs_and_rewards()
        line_2 = sale.order_line.filtered(
            lambda line: line.product_id == self.product_2
        )
        wizard = (
            self.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=sale)
            .create({"order_id": sale.id})
        )
        wizard.reward_ids = line_2.suggested_reward_ids
        reward = wizard.reward_ids.filtered(
            lambda r: r.program_id == self.loyalty_program_same_product
        )[:1]
        wizard.selected_reward_id = reward.id
        wizard.action_apply()
        self.assertEqual(
            sale.order_line.filtered(
                lambda x: x.product_id == self.product_2 and not x.is_reward_line
            ).product_uom_qty,
            2,
        )
        self.assertEqual(
            sale.order_line.filtered(
                lambda x: x.product_id == self.product_2 and x.is_reward_line
            ).product_uom_qty,
            2,
        )

    def test_04_same_product_buy2_get2_buy8_results_in_6_paid_and_2_free(self):
        # Check that if the order complies with the rules, even if the promotion is
        # suggested, the correct quantities are applied to the order lines.
        # For example: if the rule requires 2 and rewards 2 of the same product,
        # when buying 8, 6 are paid for + 2 are rewarded.
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product_2
            line_form.product_uom_qty = 8
        sale = sale_form.save()
        sale._update_programs_and_rewards()
        line_2 = sale.order_line.filtered(
            lambda line: line.product_id == self.product_2
        )
        wizard = (
            self.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=sale)
            .create({"order_id": sale.id})
        )
        wizard.reward_ids = line_2.suggested_reward_ids
        reward = wizard.reward_ids.filtered(
            lambda r: r.program_id == self.loyalty_program_same_product
        )[:1]
        wizard.selected_reward_id = reward.id
        wizard.action_apply()
        self.assertEqual(
            sale.order_line.filtered(
                lambda x: x.product_id == self.product_2 and not x.is_reward_line
            ).product_uom_qty,
            6,
        )
        self.assertEqual(
            sale.order_line.filtered(
                lambda x: x.product_id == self.product_2 and x.is_reward_line
            ).product_uom_qty,
            2,
        )
