# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import tagged

from odoo.addons.sale_coupon.tests.common import TestSaleCouponCommon


@tagged("post_install", "-at_install")
class TestSaleCouponCumulative(TestSaleCouponCommon):
    def setUp(self):
        super(TestSaleCouponCumulative, self).setUp()

        self.largeCabinet = self.env["product.product"].create(
            {
                "name": "Large Cabinet",
                "list_price": 320.0,
                "taxes_id": False,
            }
        )
        self.conferenceChair = self.env["product.product"].create(
            {
                "name": "Conference Chair",
                "list_price": 16.5,
                "taxes_id": False,
            }
        )

        self.steve = self.env["res.partner"].create(
            {
                "name": "Steve Bucknor",
                "email": "steve.bucknor@example.com",
            }
        )
        self.empty_order = self.env["sale.order"].create({"partner_id": self.steve.id})

        self.global_promo = self.env["coupon.program"].create(
            {
                "name": "10% on all orders",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 10.0,
                "program_type": "promotion_program",
                "sequence": 20,
            }
        )

    def test_program_cumulative(self):
        order = self.empty_order
        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": self.conferenceChair.id,
                "name": "Conference chair",
                "product_uom_qty": 4.0,
                "order_id": order.id,
            }
        )

        self.assertEqual(
            order.amount_total,
            386,  # 320 + 4 * 16.5
            "Before computing promotions, total should be the sum of product price.",
        )

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            347.4,  # 386 - 0.1 * 386
            2,
            "The best global discount is applied",
        )

        self.env["coupon.program"].create(
            {
                "name": "50% incredible offer",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 50.0,
                "program_type": "promotion_program",
                "sequence": 30,
            }
        )

        program = self.env["coupon.program"].create(
            {
                "name": "5% with prime program",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 5.0,
                "program_type": "promotion_program",
                "sequence": 50,
            }
        )
        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            193.0,  # 386 - 0.5 * 386
            2,
            "Only the best global discount is applied",
        )

        program.cumulative = True
        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            173.7,  # 386 - 0.5 * 386 - 0.05 * 386
            2,
            "Both global discounts are applied",
        )

    def test_program_cumulative_global_discount_coupon(self):
        order = self.empty_order
        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": self.conferenceChair.id,
                "name": "Conference chair",
                "product_uom_qty": 4.0,
                "order_id": order.id,
            }
        )
        self.env["coupon.program"].create(
            {
                "name": "5% prime",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 5.0,
                "program_type": "promotion_program",
                "sequence": 30,
                "cumulative": True,
            }
        )
        coupon_program = self.env["coupon.program"].create(
            {
                "name": "50% full sale",
                "promo_code_usage": "code_needed",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 50.0,
                "sequence": 20,
            }
        )
        self.global_promo.active = False

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            366.7,  # 386 - 0.05 * 386
            2,
            "Unapplied coupons should not be taken in account.",
        )

        self.env["coupon.generate.wizard"].with_context(
            active_id=coupon_program.id
        ).create(
            {
                "generation_type": "nbr_coupon",
                "nbr_coupons": 1,
            }
        ).generate_coupon()
        coupon = coupon_program.coupon_ids
        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": coupon.code}
        ).process_coupon()

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            173.70,  # 386 - 0.5 * 386 - 0.05 * 386
            2,
            "Applied coupons should be taken in account.",
        )
