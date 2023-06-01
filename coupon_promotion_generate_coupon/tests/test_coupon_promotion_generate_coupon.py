# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, TransactionCase


class TestCouponGenerateCoupon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        cls.other_partner = cls.partner.copy({"name": "Mr. OCA"})
        cls.product_1 = cls.env["product.product"].create(
            {"name": "Test 1", "sale_ok": True, "list_price": 50}
        )
        cls.product_2 = cls.env["product.product"].create(
            {"name": "Test 2", "sale_ok": True, "list_price": 50}
        )
        coupon_program_form = Form(
            cls.env["coupon.program"],
            view="coupon.coupon_program_view_coupon_program_form",
        )
        coupon_program_form.name = "Test coupon program with generated coupons"
        coupon_program_form.rule_products_domain = [("id", "=", cls.product_2.id)]
        cls.coupon_program = coupon_program_form.save()
        promotion_program_form = Form(
            cls.env["coupon.program"],
            view="coupon.coupon_program_view_promo_program_form",
        )
        promotion_program_form.name = "Test program with coupon generation conditions"
        promotion_program_form.promo_applicability = "on_next_order"
        promotion_program_form.rule_products_domain = [("id", "=", cls.product_1.id)]
        promotion_program_form.next_order_program_id = cls.coupon_program
        promotion_program_form.promo_code_usage = "no_code_needed"
        cls.promotion_program = promotion_program_form.save()
