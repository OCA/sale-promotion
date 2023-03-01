# Copyright 2023 Tecnativa - Stefan Ungureanu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.coupon_incompatibility.tests.test_coupon_incompatibility import (
    CouponIncompatibilityCase,
)


class TestCouponIncompatibility(CouponIncompatibilityCase):
    def _create_coupon_program(self, product=False, code=False, apply_on_order=True):
        """Helper method to create coupon programs in the tests cases"""
        coupon_program_form = Form(
            self.env["coupon.program"],
            view="sale_coupon.sale_coupon_program_view_promo_program_form",
        )
        coupon_program_form.name = "Test Coupon Incompatibility"
        if product:
            # We don't want demo programs spoiling our tests
            coupon_program_form.rule_products_domain = "[('id', '=', %s)]" % (
                product.id
            )
        if not code:
            coupon_program_form.promo_code_usage = "no_code_needed"
        else:
            coupon_program_form.promo_code_usage = "code_needed"
            coupon_program_form.promo_code = code
        if apply_on_order:
            coupon_program_form.promo_applicability = "on_current_order"
        else:
            coupon_program_form.promo_applicability = "next_order"
        coupon_program_form.reward_type = "product"
        coupon_program_form.reward_product_id = product or self.product_a
        return coupon_program_form.save()

    def _generate_coupons(self, program, number=1):
        """Helper method to easily generate coupons in the test cases"""
        self.env["coupon.generate.wizard"].with_context(active_id=program.id).create(
            {"generation_type": "nbr_coupon", "nbr_coupons": number}
        ).generate_coupon()
        return program.coupon_ids

    def _create_sale(self, partner, products=False):
        """Helper method to create sales in the test cases"""
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = partner
        if not products:
            products = self.product_a
        for product in products:
            with sale_form.order_line.new() as line_form:
                line_form.product_id = product
                line_form.product_uom_qty = 3
        return sale_form.save()

    def _apply_coupon(self, order, code, bp=False):
        """Helper method to apply either coupon or progam codes. It ensures that the
        UserError exception is raised as well."""
        self.env["sale.coupon.apply.code"].with_context(
            active_id=order.id, bp=bp
        ).create({"coupon_code": code}).process_coupon()

    def test_01_program_incompatibilities(self):
        """A program with no code and customer application limit won't be applied
        once the limit is reached"""
        # First we test the regular behavior
        promotion_1 = self._create_coupon_program(self.product_a, code="TEST-00000002")
        promotion_2 = self._create_coupon_program(self.product_b, code="TEST-00000003")
        coupons_2 = (x for x in self._generate_coupons(promotion_2, 2))
        promotion_3 = self._create_coupon_program(self.product_c, code="TEST-00000004")
        coupons_3 = (x for x in self._generate_coupons(promotion_3, 2))
        sale_1 = self._create_sale(
            self.partner_1, (self.product_a + self.product_b + self.product_c)
        )
        # Apply the promotions
        self._apply_coupon(sale_1, "TEST-00000002")
        self._apply_coupon(sale_1, next(coupons_2).code)
        self._apply_coupon(sale_1, next(coupons_3).code)
        # A discount line is create for each promotion
        self.assertEqual(len(sale_1.order_line.filtered("is_reward_line")), 3)
        # Let's create another sale and set some incompatibilities
        promotion_1.incompatible_promotion_ids = promotion_2
        # The incompatibility is reciprocal
        self.assertEqual(promotion_2.incompatible_promotion_ids, promotion_1)
        sale_2 = self._create_sale(
            self.partner_1, (self.product_a + self.product_b + self.product_c)
        )
        self._apply_coupon(sale_2, "TEST-00000002")
        # The coupon program isn't compatible anymore
        last_coupon_2_code = next(coupons_2)
        with self.assertRaises(UserError):
            self._apply_coupon(sale_2, last_coupon_2_code.code)
        # We can still apply the promotion 3 coupons anyway:
        self._apply_coupon(sale_2, next(coupons_3).code)
        # Remove the incompatibility from either promotion
        promotion_2.incompatible_promotion_ids = False
        self.assertFalse(promotion_1.incompatible_promotion_ids)
        # We can now apply it without restrictions
        self._apply_coupon(sale_2, last_coupon_2_code.code)
