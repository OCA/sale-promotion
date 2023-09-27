# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form

from odoo.addons.loyalty_limit.tests.test_loyalty_limit import LoyaltyLimitCase


class TestSaleCouponLimit(LoyaltyLimitCase):
    def _action_apply_program(self, sale, program):
        sale._update_programs_and_rewards()
        wizard = (
            self.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=sale)
            .create({"selected_reward_id": program.reward_ids.id})
        )
        wizard.action_apply()

    def _create_sale(self, partner, salesman=False):
        """Helper method to create sales in the test cases"""
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = partner
        if salesman:
            sale_form.user_id = salesman
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product_a
            line_form.product_uom_qty = 1
        return sale_form.save()

    def _apply_promo_code(self, order, code, no_reward_fail=True):
        status = order._try_apply_code(code)
        if "error" in status:
            raise ValidationError(status["error"])
        coupons = self.env["loyalty.card"]
        rewards = self.env["loyalty.reward"]
        for coupon, coupon_rewards in status.items():
            coupons |= coupon
            rewards |= coupon_rewards
        if len(coupons) == 1 and len(rewards) == 1:
            status = order._apply_program_reward(rewards, coupons)

    def test_01_program_no_code_customer_limit(self):
        """A program with no code and customer application limit won't be applied
        once the limit is reached"""
        sale_1 = self._create_sale(self.partner_1)
        # In the case definition the program is no code, so there's nothing else to
        # setup.
        self._action_apply_program(sale_1, self.promotion_with_customer_limit)
        self.assertTrue(bool(sale_1.order_line.filtered("is_reward_line")))
        # The limit is 2, so the promotion can be placed in a second order
        sale_2 = self._create_sale(self.partner_1)
        self._action_apply_program(sale_2, self.promotion_with_customer_limit)
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        # As we reach the limit, no discount will be applied
        sale_3 = self._create_sale(self.partner_1)
        with self.assertRaises(ValidationError):
            self._action_apply_program(sale_3, self.promotion_with_customer_limit)
        self.assertFalse(bool(sale_3.order_line.filtered("is_reward_line")))
        # However other partners can still enjoy the promotion
        sale_4 = self._create_sale(self.partner_2)
        self._action_apply_program(sale_4, self.promotion_with_customer_limit)
        self.assertTrue(bool(sale_4.order_line.filtered("is_reward_line")))

    def test_02_program_promo_code_customer_limit(self):
        """A program with code and customer application limit will raise an error when
        # such limit is reached for a customer"""
        self.promotion_with_customer_limit.program_type = "promo_code"
        self.promotion_with_customer_limit.rule_ids.code = "TEST-SALE-COUPON-LIMIT"
        self.promotion_with_customer_limit.reward_ids.discount_product_ids = (
            self.product_a
        )
        # We apply it once for partner 1...
        sale_1 = self._create_sale(self.partner_1)
        self._apply_promo_code(sale_1, "TEST-SALE-COUPON-LIMIT")
        self.assertTrue(bool(sale_1.order_line.filtered("is_reward_line")))
        # We apply it twice for partner 1...
        sale_2 = self._create_sale(self.partner_1)
        self._apply_promo_code(sale_2, "TEST-SALE-COUPON-LIMIT")
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        # As we reach the limit we can't apply this code anymore
        sale_3 = self._create_sale(self.partner_1)
        with self.assertRaises(ValidationError):
            self._apply_promo_code(sale_3, "TEST-SALE-COUPON-LIMIT")
        # We can still apply the promotion to other partners
        sale_4 = self._create_sale(self.partner_2)
        self._apply_promo_code(sale_4, "TEST-SALE-COUPON-LIMIT")
        self.assertTrue(bool(sale_4.order_line.filtered("is_reward_line")))

    def test_03_coupon_code_customer_limit(self):
        """When a coupon of a customer limited program is applied, an error will raise
        when the limit is reached for a given customer."""
        # Create coupons for the coupon program
        self.env["loyalty.generate.wizard"].with_context(
            active_id=self.coupon_program_with_customer_limit.id
        ).create({"coupon_qty": 3}).generate_coupons()
        coupon1, coupon2, coupon3 = self.coupon_program_with_customer_limit.coupon_ids
        sale_1 = self._create_sale(self.partner_1)
        self._apply_promo_code(sale_1, coupon1.code)
        self.assertTrue(bool(sale_1.order_line.filtered("is_reward_line")))
        # We apply another coupon for partner 1...
        sale_2 = self._create_sale(self.partner_1)
        self._apply_promo_code(sale_2, coupon2.code)
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        # No coupon is applied. In Backend UI a Warning popup is raised
        sale_3 = self._create_sale(self.partner_1)
        with self.assertRaises(ValidationError):
            self._apply_promo_code(sale_3, coupon3.code)
        # We can still apply the coupon to other partners
        sale_4 = self._create_sale(self.partner_2)
        self._apply_promo_code(sale_4, coupon3.code)
        self.assertTrue(bool(sale_4.order_line.filtered("is_reward_line")))

    def test_04_coupon_code_next_order_customer_limit(self):
        """Coupons should not be generated for next orders above the customer limit"""
        # The first order generates the coupon for the next one
        sale_1 = self._create_sale(self.partner_1)
        sale_1._update_programs_and_rewards()
        sale_1.action_confirm()
        coupon_1 = self.next_order_coupon_with_customer_limit.coupon_ids
        self.assertTrue(bool(coupon_1.points > 0), "A valid coupon must be generated")
        # Apply it and generate another coupon in a second sale and apply it again
        self._apply_promo_code(self._create_sale(self.partner_1), coupon_1.code)
        sale_2 = self._create_sale(self.partner_1)
        sale_2._update_programs_and_rewards()
        sale_2.action_confirm()
        coupon_2 = self.next_order_coupon_with_customer_limit.coupon_ids[1]
        self.assertTrue(
            bool(coupon_2.points > 0), "A second valid coupon must be generated"
        )
        self._apply_promo_code(self._create_sale(self.partner_1), coupon_2.code)
        # Finally, we can't generate more coupons from this promotion for this partner
        sale_3 = self._create_sale(self.partner_1)
        sale_3._update_programs_and_rewards()
        sale_3.action_confirm()
        self.assertFalse(
            bool(len(self.next_order_coupon_with_customer_limit.coupon_ids) > 2),
            "No more coupons should be generated for this customer and program",
        )
        # Other customers can still use the program
        sale_4 = self._create_sale(self.partner_2)
        sale_4._update_programs_and_rewards()
        sale_4.action_confirm()
        coupon_4 = self.next_order_coupon_with_customer_limit.coupon_ids[2]
        self.assertTrue(
            bool(coupon_4.points > 0),
            "A valid coupon should be generated for this customer",
        )

    def test_05_program_no_code_salesman_limit(self):
        """A program with no code and salesman application limit won't be applied
        once the limit is reached"""
        # Avoid other salesmen using this program
        self.promotion_with_salesman_limit.salesmen_strict_limit = True
        # Place the first order of salesman 1
        sale_1 = self._create_sale(self.partner_1, self.salesman_1)
        self._action_apply_program(sale_1, self.promotion_with_salesman_limit)
        self.assertTrue(bool(sale_1.order_line.filtered("is_reward_line")))
        # The limit is 2, so the promotion can be placed in a second order
        sale_2 = self._create_sale(self.partner_1, self.salesman_1)
        self._action_apply_program(sale_2, self.promotion_with_salesman_limit)
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        # As we reach the limit, no discount will be applied
        sale_3 = self._create_sale(self.partner_1, self.salesman_1)
        with self.assertRaises(ValidationError):
            self._action_apply_program(sale_3, self.promotion_with_salesman_limit)
        self.assertFalse(bool(sale_3.order_line.filtered("is_reward_line")))
        # However the other salesman can still enjoy the promotion
        sale_4 = self._create_sale(self.partner_1, self.salesman_2)
        self._action_apply_program(sale_4, self.promotion_with_salesman_limit)
        self.assertTrue(bool(sale_4.order_line.filtered("is_reward_line")))
        # As only the salesmen in the list can use the promotion, no other can apply it
        sale_5 = self._create_sale(self.partner_1)
        with self.assertRaises(ValidationError):
            self._action_apply_program(sale_5, self.promotion_with_salesman_limit)
        self.assertFalse(bool(sale_5.order_line.filtered("is_reward_line")))

    def test_06_program_promo_code_salesman_limit(self):
        """A program with code and salesman application limit will raise an error when
        such limit is reached for a salesman in the list"""
        self.promotion_with_salesman_limit.program_type = "promo_code"
        self.promotion_with_salesman_limit.trigger = "with_code"
        self.promotion_with_salesman_limit.applies_on = "current"
        self.promotion_with_salesman_limit.salesmen_strict_limit = True
        self.promotion_with_salesman_limit.rule_ids.mode = "with_code"
        self.promotion_with_salesman_limit.rule_ids.code = "TEST-SALE-COUPON-LIMIT"
        self.promotion_with_salesman_limit.reward_ids.discount_product_ids = (
            self.product_a
        )
        # First salesman_1 order...
        sale_1 = self._create_sale(self.partner_1, self.salesman_1)
        self._apply_promo_code(sale_1, "TEST-SALE-COUPON-LIMIT")
        self.assertTrue(bool(sale_1.order_line.filtered("is_reward_line")))
        # Second salesman_1 order...
        sale_2 = self._create_sale(self.partner_1, self.salesman_1)
        self._apply_promo_code(sale_2, "TEST-SALE-COUPON-LIMIT")
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        # As we reach the limit we can't apply this code anymore
        sale_3 = self._create_sale(self.partner_1, self.salesman_1)
        with self.assertRaises(ValidationError):
            self._apply_promo_code(sale_3, "TEST-SALE-COUPON-LIMIT")
        # We can still apply the promotion with the other salesman
        sale_4 = self._create_sale(self.partner_1, self.salesman_2)
        self._apply_promo_code(sale_4, "TEST-SALE-COUPON-LIMIT")
        self.assertTrue(bool(sale_4.order_line.filtered("is_reward_line")))
        # But only the salesmen in the list can use the promotion, no other can apply it
        sale_5 = self._create_sale(self.partner_1)
        with self.assertRaises(ValidationError):
            self._apply_promo_code(sale_5, "TEST-SALE-COUPON-LIMIT")

    def test_07_coupon_code_salesman_limit(self):
        """When a coupon of a salesmen limited program is applied, an error will raise
        when the limit is reached for a given salesman."""
        # Avoid other salesmen using this program
        self.coupon_program_with_salesman_limit.salesmen_strict_limit = True
        # Create coupons for the coupon program
        self.env["loyalty.generate.wizard"].with_context(
            active_id=self.coupon_program_with_salesman_limit.id
        ).create({"coupon_qty": 3}).generate_coupons()
        coupon1, coupon2, coupon3 = self.coupon_program_with_salesman_limit.coupon_ids
        # We apply one coupon with salesman_1...
        sale_1 = self._create_sale(self.partner_1, self.salesman_1)
        self._apply_promo_code(sale_1, coupon1.code)
        self.assertTrue(bool(sale_1.order_line.filtered("is_reward_line")))
        # We apply another coupon with salesman_1...
        sale_2 = self._create_sale(self.partner_1, self.salesman_1)
        self._apply_promo_code(sale_2, coupon2.code)
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        # An error raises as we reach the limit
        sale_3 = self._create_sale(self.partner_1, self.salesman_1)
        with self.assertRaises(UserError):
            self._apply_promo_code(sale_3, coupon3.code)
        # We can't apply with salesmen not in the list either
        sale_4 = self._create_sale(self.partner_1)
        with self.assertRaises(UserError):
            self._apply_promo_code(sale_4, coupon3.code)
        # We can still apply the coupon with salesman_2
        sale_5 = self._create_sale(self.partner_1, self.salesman_2)
        self._apply_promo_code(sale_5, coupon3.code)
        self.assertTrue(bool(sale_5.order_line.filtered("is_reward_line")))

    def test_08_coupon_code_next_order_salesmen_limit(self):
        """Coupons should not be generated for next orders above the salesman limit"""
        # Avoid other salesmen using this program
        self.next_order_coupon_with_salesman_limit.salesmen_strict_limit = True
        # The first order generates the coupon for the next one
        sale_1 = self._create_sale(self.partner_1, self.salesman_1)
        sale_1._update_programs_and_rewards()
        sale_1.action_confirm()
        coupon_1 = self.next_order_coupon_with_salesman_limit.coupon_ids[0]
        self.assertTrue(bool(coupon_1.points > 0), "A valid coupon must be generated")
        # Apply it and generate another coupon in a second sale and apply it again
        self._apply_promo_code(
            self._create_sale(self.partner_1, self.salesman_1), coupon_1.code
        )
        sale_2 = self._create_sale(self.partner_1, self.salesman_1)
        sale_2._update_programs_and_rewards()
        sale_2.action_confirm()
        coupon_2 = self.next_order_coupon_with_salesman_limit.coupon_ids[1]
        self.assertTrue(
            bool(coupon_2.points > 0), "A second valid coupon must be generated"
        )
        self._apply_promo_code(
            self._create_sale(self.partner_1, self.salesman_1), coupon_2.code
        )
        # Finally, we can't generate more coupons from this promotion for this partner
        sale_3 = self._create_sale(self.partner_1, self.salesman_1)
        sale_3._update_programs_and_rewards()
        self.assertFalse(
            bool(len(self.next_order_coupon_with_salesman_limit.coupon_ids) > 2),
            "No more coupons should be generated for this salesman and program",
        )
        # Other customers can still use the program
        sale_4 = self._create_sale(self.partner_1, self.salesman_2)
        sale_4._update_programs_and_rewards()
        sale_4.action_confirm()
        coupon_4 = self.next_order_coupon_with_salesman_limit.coupon_ids[2]
        self.assertTrue(
            bool(coupon_4.points > 0),
            "A valid coupon should be generated for this customer",
        )
