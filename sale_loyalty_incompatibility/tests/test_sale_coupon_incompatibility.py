# Copyright 2023 Tecnativa - Stefan Ungureanu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.sale_loyalty.tests.common import TestSaleCouponCommon


class TestLoyaltyIncompatibility(TestSaleCouponCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.promotion_1 = cls.code_promotion_program
        cls.promotion_2 = cls.code_promotion_program.copy()
        cls.promotion_2.rule_ids.write({"product_ids": cls.product_C})
        cls.env["loyalty.generate.wizard"].with_context(
            active_id=cls.promotion_1
        ).create(
            {
                "mode": "selected",
                "customer_ids": cls.steve,
                "points_granted": 1,
            }
        ).generate_coupons()
        cls.coupon_promotion_1 = cls.promotion_1.coupon_ids
        cls.env["loyalty.generate.wizard"].with_context(
            active_id=cls.promotion_2
        ).create(
            {
                "mode": "selected",
                "customer_ids": cls.steve,
                "points_granted": 1,
            }
        ).generate_coupons()
        cls.coupon_promotion_2 = cls.promotion_2.coupon_ids
        cls.order = cls.empty_order
        sale_form = Form(cls.order)
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_A
            line_form.name = "1 Product A"
            line_form.product_uom = cls.uom_unit
            line_form.product_uom_qty = 1.0
        sale_form.save()

    def test_01_program_incompatibilities(self):
        """A program with no code and customer application limit won't be applied
        once the limit is reached"""
        # First we test the regular behavior
        # Test basic case for coupon program with code
        self.code_promotion_program.reward_ids.reward_type = "discount"
        self.code_promotion_program.reward_ids.discount = 10

        self._apply_promo_code(self.order, self.coupon_promotion_1.code)
        self.assertEqual(len(self.order.order_line.ids), 2)
        # Set some incompatibilities between promotion_1 and promotion_2
        # First validate that's inverted process works fine
        self.promotion_1.incompatible_promotion_ids = self.promotion_2
        self.assertEqual(self.promotion_2.incompatible_promotion_ids, self.promotion_1)
        # Add product C for try apply booth coupon programs same time
        sale_form = Form(self.order)
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product_C
            line_form.name = "1 Product C"
            line_form.product_uom = self.uom_unit
            line_form.product_uom_qty = 1.0
        sale_form.save()
        # Second we will try to apply two programs with incompatibility between themselves
        # The coupon program isn't compatible anymore
        with self.assertRaises(UserError):
            self._apply_promo_code(self.order, self.coupon_promotion_2.code)
        # Remove last coupon from promotion_1 applied
        self.order.order_line.filtered("is_reward_line").unlink()
        # Remove the incompatibility from either promotion
        self.promotion_2.incompatible_promotion_ids = False
        self.assertFalse(self.promotion_1.incompatible_promotion_ids)
        # We can now apply it without restrictions
        self._apply_promo_code(self.order, self.coupon_promotion_2.code)
