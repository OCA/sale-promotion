# Copyright 2021 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form

from odoo.addons.loyalty_multi_gift.tests.test_loyalty_multi_gift_case import (
    LoyaltyMultiGiftCase,
)


class TestSaleLoyaltyMultiGift(LoyaltyMultiGiftCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_1
            line_form.product_uom_qty = 2
        cls.sale = sale_form.save()

    def _action_apply_program(self, sale, program, reward_line_options=False):
        sale._update_programs_and_rewards()
        wizard = (
            self.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=sale)
            .create({"selected_reward_id": program.reward_ids[0].id})
        )
        if reward_line_options:
            for line in wizard.loyalty_gift_line_ids:
                line.selected_gift_id = reward_line_options.get(line.line_id.id)
        wizard.action_apply()

    def test_01_sale_coupon_test_multi_gift(self):
        """As we fulfill the proper product qties, we get the proper free product"""
        self._action_apply_program(self.sale, self.loyalty_program_form)
        # As set up, we should one discount line for every reward line in the promotion
        discount_line_product_2 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_2 and x.is_reward_line
        )
        discount_line_product_3 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_3 and x.is_reward_line
        )
        self.assertEqual(2, discount_line_product_2.product_uom_qty)
        self.assertEqual(3, discount_line_product_3.product_uom_qty)
        self.assertEqual(60, discount_line_product_2.price_unit)
        self.assertEqual(70, discount_line_product_3.price_unit)

    def test_02_test_sale_coupon_test_multi_gift(self):
        line = self.sale.order_line
        line_form = Form(line, view="sale.view_order_line_tree")
        line_form.product_uom_qty = 7
        line_form.save()
        self._action_apply_program(self.sale, self.loyalty_program_form)
        discount_line_product_2 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_2 and x.is_reward_line
        )
        discount_line_product_3 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_3 and x.is_reward_line
        )
        # The promotion will only be applied once whatever the min quantity
        self.assertEqual(2, discount_line_product_2.product_uom_qty)
        self.assertEqual(3, discount_line_product_3.product_uom_qty)

    def test_03_test_sale_coupon_test_multi_gift(self):
        line = self.sale.order_line
        line_form = Form(line, view="sale.view_order_line_tree")
        # Now it can't be applied anymore so the discount lines will dissapear
        line_form.product_uom_qty = 1
        line_form.save()
        self.sale._update_programs_and_rewards()
        discount_line = self.sale.order_line.filtered("is_reward_line")
        # The discount goes away
        self.assertFalse(bool(discount_line))

    def test_04_test_sale_coupon_test_multi_gift(self):
        # Optional rewards
        reward_line_options = {
            self.loyalty_program_form.reward_ids[0]
            .loyalty_multi_gift_ids[0]
            .id: self.product_2.id,
            self.loyalty_program_form.reward_ids[0]
            .loyalty_multi_gift_ids[1]
            .id: self.product_4.id,
        }
        self._action_apply_program(
            self.sale,
            self.loyalty_program_form,
            reward_line_options=reward_line_options,
        )
        discount_line_product_2 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_2 and x.is_reward_line
        )
        discount_line_product_3 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_3 and x.is_reward_line
        )
        discount_line_product_4 = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_4 and x.is_reward_line
        )
        self.assertEqual(2, discount_line_product_2.product_uom_qty)
        self.assertEqual(3, discount_line_product_4.product_uom_qty)
        self.assertFalse(discount_line_product_3)

    def test_05_test_loyalty_gift_line_ids_computation(self):
        """Test the computation of loyalty_gift_line_ids for a multi_gift reward."""
        self.loyalty_program_form.reward_ids[0].write({"reward_type": "multi_gift"})
        # Create wizard
        wizard = (
            self.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=self.sale.id)
            .create({"selected_reward_id": self.loyalty_program_form.reward_ids[0].id})
        )
        # Assert loyalty_gift_line_ids computation
        self.assertTrue(
            wizard.loyalty_gift_line_ids, "Loyalty Gift Line IDs should be computed."
        )
        self.assertEqual(
            len(wizard.loyalty_gift_line_ids),
            len(self.loyalty_program_form.reward_ids[0].loyalty_multi_gift_ids),
            "Loyalty Gift Line IDs count mismatch.",
        )

    def test_06_test_action_apply_no_reward_selected(self):
        """Test the action_apply method with no reward selected."""
        wizard = (
            self.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=self.sale.id)
            .create({})
        )
        with self.assertRaises(ValidationError):
            wizard.action_apply()

    def test_07_test_action_apply_no_coupon_found(self):
        """Test the action_apply method when no coupon is found."""
        self.loyalty_program_form.reward_ids[0].write({"reward_type": "multi_gift"})
        wizard = (
            self.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=self.sale.id)
            .create({"selected_reward_id": self.loyalty_program_form.reward_ids[0].id})
        )
        with self.assertRaises(ValidationError):
            wizard.action_apply()

    def test_08_test_action_apply_non_multi_gift_reward(self):
        """Test the action_apply method with a non-multi_gift reward."""
        self.loyalty_program_form.reward_ids[0].write({"reward_type": "discount"})
        wizard = (
            self.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=self.sale.id)
            .create({"selected_reward_id": self.loyalty_program_form.reward_ids[0].id})
        )
        with self.assertRaises(ValidationError):
            wizard.action_apply()

    def test_09_invalid_product_in_reward(self):
        """Test invalid product in reward during multi-gift reward line creation."""
        # Create a valid coupon for the reward program
        coupon = self.env["loyalty.card"].create(
            {
                "program_id": self.loyalty_program_form.id,
                "code": "VALID_COUPON",
                "points": 10,
            }
        )

        # Get the reward from the program
        reward = self.loyalty_program_form.reward_ids[0]

        # Create an invalid product to test with
        invalid_product = self.env["product.product"].create(
            {"name": "Invalid Product", "list_price": 100.0}
        )

        # Simulate a scenario where the selected product is
        # not in the reward's valid products.
        with self.assertRaises(UserError):
            self.sale._get_reward_values_multi_gift_line(
                reward,
                coupon,
                cost=100,
                reward_line=self.loyalty_program_form.reward_ids[
                    0
                ].loyalty_multi_gift_ids[0],
                product=invalid_product,
            )
