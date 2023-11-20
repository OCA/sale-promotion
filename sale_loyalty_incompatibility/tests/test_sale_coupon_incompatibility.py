# Copyright 2023 Tecnativa - Stefan Ungureanu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests import Form

from odoo.addons.loyalty_incompatibility.tests.test_loyalty_incompatibility import (
    LoyaltyIncompatibilityCase,
)


class TestSaleLoyaltyIncompatibility(LoyaltyIncompatibilityCase):
    def _action_apply_program(self, sale, program):
        sale._update_programs_and_rewards()
        wizard = (
            self.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=sale.id)
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

    def test_01_program_without_incompatibilities(self):
        """When there are no incompatibilities, both coupons and promotions can be applied
        to the same sales order."""
        # Create coupons for the coupon program
        self.env["loyalty.generate.wizard"].with_context(
            active_id=self.coupon_program_without_incompatibility.id
        ).create({"coupon_qty": 1}).generate_coupons()
        coupon = self.coupon_program_without_incompatibility.coupon_ids
        sale = self._create_sale(self.partner)
        # Apply promotion and coupon
        self._action_apply_program(sale, self.promotion)
        self._apply_promo_code(sale, coupon.code)
        self.assertTrue(len(sale.order_line.filtered("is_reward_line")) == 2)

    def test_02_program_with_incompatibilities(self):
        """When an incompatible promotion is set up, the incompatible promotion cannot be
        applied with the coupons."""
        # Create coupons for the coupon program
        self.env["loyalty.generate.wizard"].with_context(
            active_id=self.coupon_program_with_incompatibility.id
        ).create({"coupon_qty": 1}).generate_coupons()
        coupon = self.coupon_program_with_incompatibility.coupon_ids
        sale = self._create_sale(self.partner)
        # Apply promotion
        self._action_apply_program(sale, self.promotion)
        # The coupon cannot be applied.
        with self.assertRaises(ValidationError):
            self._apply_promo_code(sale, coupon.code)
        # Remove reward from incompatible promotion to be able to apply the coupon
        sale.order_line.filtered("is_reward_line").unlink()
        self._apply_promo_code(sale, coupon.code)
        # Once the coupon has been applied the promotion cannot be applied.
        with self.assertRaises(ValidationError):
            self._action_apply_program(sale, self.promotion)
