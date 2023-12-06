# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import tagged

from odoo.addons.sale_coupon.tests.common import TestSaleCouponCommon


@tagged("post_install", "-at_install")
class TestSaleCouponApplyOnDomain(TestSaleCouponCommon):
    def setUp(self):
        super(TestSaleCouponApplyOnDomain, self).setUp()

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

        self.drawer = self.env["product.product"].create(
            {
                "name": "Drawer Light",
                "list_price": 25.0,
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

        self.promo = self.env["coupon.program"].create(
            {
                "name": "20% reduction on products with a C letter",
                "promo_code_usage": "no_code_needed",
                "reward_type": "discount",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 20.0,
                "discount_apply_on": "product_domain",
                "discount_product_domain": '[["name","ilike","C"]]',
            }
        )

    def make_order(self):
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
                "name": "Conference Chair",
                "product_uom_qty": 8.0,
                "order_id": order.id,
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": self.drawer.id,
                "name": "Drawer Light",
                "product_uom_qty": 2.0,
                "order_id": order.id,
            }
        )
        return order

    def test_program_apply_on_domain_for_coupon(self):
        order = self.make_order()

        self.promo.promo_code_usage = "code_needed"
        self.promo.program_type = "coupon_program"

        self.assertAlmostEqual(
            order.amount_total,
            502,  # 320 + 8 * 16.5 + 2 * 25
            2,
            "Before computing promotions, total should be the sum of product price.",
        )

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            502,  # 320 + 8 * 16.5 + 2 * 25
            2,
            "Before applying coupon, total should be the sum of product price.",
        )

        self.env["coupon.generate.wizard"].with_context(active_id=self.promo.id).create(
            {
                "generation_type": "nbr_coupon",
                "nbr_coupons": 1,
            }
        ).generate_coupon()
        coupon = self.promo.coupon_ids

        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": coupon.code}
        ).process_coupon()

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            411.6,  # 320 + 8 * 16.5 + 2 * 25 - .2 * (320 + 8 * 16.5)
            2,
            "The coupon should apply on Large Cabinet and Conference Chair",
        )
        lines = list(order.order_line)
        self.assertEqual(len(lines), 4, "Order should have 4 lines.")
        self.assertEqual(lines[0].name, "Large Cabinet")
        self.assertAlmostEqual(lines[0].price_total, 320.0)
        self.assertEqual(lines[1].name, "Conference Chair")
        self.assertAlmostEqual(lines[1].price_total, 132.0)
        self.assertEqual(lines[2].name, "Drawer Light")
        self.assertAlmostEqual(lines[2].price_total, 50.0)
        self.assertIn("Discount: 20%", lines[3].name)
        self.assertAlmostEqual(lines[3].price_total, -90.4)

    def test_program_apply_on_domain_for_promotion(self):
        order = self.make_order()

        self.assertAlmostEqual(
            order.amount_total,
            502,  # 320 + 8 * 16.5 + 2 * 25
            2,
            "Before computing promotions, total should be the sum of product price.",
        )

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            411.6,  # 320 + 8 * 16.5 + 2 * 25 - .2 * (320 + 8 * 16.5)
            2,
            "The promotion should apply on Large Cabinet and Conference Chair",
        )
        lines = list(order.order_line)
        self.assertEqual(len(lines), 4, "Order should have 4 lines.")
        self.assertEqual(lines[0].name, "Large Cabinet")
        self.assertAlmostEqual(lines[0].price_total, 320.0)
        self.assertEqual(lines[1].name, "Conference Chair")
        self.assertAlmostEqual(lines[1].price_total, 132.0)
        self.assertEqual(lines[2].name, "Drawer Light")
        self.assertAlmostEqual(lines[2].price_total, 50.0)
        self.assertIn("Discount: 20%", lines[3].name)
        self.assertAlmostEqual(lines[3].price_total, -90.4)

    def test_program_apply_on_domain_for_promotion_with_w_rule(self):
        order = self.make_order()

        self.promo.discount_product_domain = '[["name","ilike","w"]]'

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            492,  # 320 + 8 * 16.5 + 2 * 25 - .2 * (2 * 25)
            2,
            "The promotion should apply on Drawer Light",
        )
        lines = list(order.order_line)
        self.assertEqual(len(lines), 4, "Order should have 4 lines.")
        self.assertEqual(lines[0].name, "Large Cabinet")
        self.assertAlmostEqual(lines[0].price_total, 320.0)
        self.assertEqual(lines[1].name, "Conference Chair")
        self.assertAlmostEqual(lines[1].price_total, 132.0)
        self.assertEqual(lines[2].name, "Drawer Light")
        self.assertAlmostEqual(lines[2].price_total, 50.0)
        self.assertIn("Discount: 20%", lines[3].name)
        self.assertAlmostEqual(lines[3].price_total, -10)

    def test_program_apply_on_domain_for_promotion_with_l_rule(self):
        order = self.make_order()
        self.promo.discount_product_domain = '[["name","ilike","l"]]'

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            428,  # 320 + 8 * 16.5 + 2 * 25 - .2 * (320 + 2 * 25)
            2,
            "The promotion should apply on Large Cabinet and Drawer Light",
        )
        lines = list(order.order_line)
        self.assertEqual(len(lines), 4, "Order should have 4 lines.")
        self.assertEqual(lines[0].name, "Large Cabinet")
        self.assertAlmostEqual(lines[0].price_total, 320.0)
        self.assertEqual(lines[1].name, "Conference Chair")
        self.assertAlmostEqual(lines[1].price_total, 132.0)
        self.assertEqual(lines[2].name, "Drawer Light")
        self.assertAlmostEqual(lines[2].price_total, 50.0)
        self.assertIn("Discount: 20%", lines[3].name)
        self.assertAlmostEqual(lines[3].price_total, -74)

    def test_program_apply_on_domain_for_promotion_with_a_rule(self):
        order = self.make_order()
        self.promo.discount_product_domain = '[["name","ilike","a"]]'

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            401.6,  # 320 + 8 * 16.5 + 2 * 25 - .2 * (320 + 8 * 16.5 + 2 * 25)
            2,
            "The promotion should apply on all",
        )
        lines = list(order.order_line)
        self.assertEqual(len(lines), 4, "Order should have 4 lines.")
        self.assertEqual(lines[0].name, "Large Cabinet")
        self.assertAlmostEqual(lines[0].price_total, 320.0)
        self.assertEqual(lines[1].name, "Conference Chair")
        self.assertAlmostEqual(lines[1].price_total, 132.0)
        self.assertEqual(lines[2].name, "Drawer Light")
        self.assertAlmostEqual(lines[2].price_total, 50.0)
        self.assertIn("Discount: 20%", lines[3].name)
        self.assertAlmostEqual(lines[3].price_total, -100.4)

    def test_program_apply_on_domain_for_promotion_with_x_rule(self):
        order = self.make_order()
        self.promo.discount_product_domain = '[["name","ilike","x"]]'

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            502,  # 320 + 8 * 16.5 + 2 * 25
            2,
            "The promotion should apply on none",
        )
        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")
        self.assertEqual(lines[0].name, "Large Cabinet")
        self.assertAlmostEqual(lines[0].price_total, 320.0)
        self.assertEqual(lines[1].name, "Conference Chair")
        self.assertAlmostEqual(lines[1].price_total, 132.0)
        self.assertEqual(lines[2].name, "Drawer Light")
        self.assertAlmostEqual(lines[2].price_total, 50.0)

    def test_program_apply_on_domain_program_filter(self):
        order = self.make_order()
        self.assertEquals(order._get_applicable_no_code_promo_program(), self.promo)
        chair = self.env["coupon.program"].create(
            {
                "name": "reward chair",
                "promo_code_usage": "no_code_needed",
                "reward_type": "discount",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 20.0,
                "discount_apply_on": "product_domain",
                "discount_product_domain": '[["name","ilike","chair"]]',
            }
        )
        self.env["coupon.program"].create(
            {
                "name": "reward table",
                "promo_code_usage": "no_code_needed",
                "reward_type": "discount",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 10.0,
                "discount_apply_on": "product_domain",
                "discount_product_domain": '[["name","ilike","table"]]',
            }
        )
        self.env["coupon.program"].create(
            {
                "name": "reward window",
                "promo_code_usage": "no_code_needed",
                "reward_type": "discount",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 25.0,
                "discount_apply_on": "product_domain",
                "discount_product_domain": '[["name","ilike","window"]]',
            }
        )
        drawer = self.env["coupon.program"].create(
            {
                "name": "reward drawer",
                "promo_code_usage": "no_code_needed",
                "reward_type": "discount",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 1.0,
                "discount_apply_on": "product_domain",
                "discount_product_domain": '[["name","ilike","drawer"]]',
            }
        )
        self.assertEquals(
            order._get_applicable_no_code_promo_program(),
            self.env["coupon.program"].browse([self.promo.id, chair.id, drawer.id]),
        )
