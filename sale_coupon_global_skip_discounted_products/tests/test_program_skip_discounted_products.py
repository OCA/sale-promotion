# Copyright 2021-2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.sale_coupon.tests.common import TestSaleCouponCommon


@tagged("post_install", "-at_install")
class TestSaleCouponSkipDiscountedProducts(TestSaleCouponCommon):
    def setUp(self):
        super(TestSaleCouponSkipDiscountedProducts, self).setUp()

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

        self.drawerBlack = self.env["product.product"].create(
            {
                "name": "Drawer Black",
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

    def test_program_skip_discounted_products(self):
        order = self.empty_order
        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Discounted Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
                "discount": 50.0,
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
            226.0,  # 320/2 + 4 * 16.5
            "Before computing promotions, total should be the sum of product price.",
        )

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            203.4,  # 226 - 0.1 * 226
            2,
            "The global discount is applied",
        )

        self.global_promo.skip_discounted_products = True

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            219.4,  # 226 - 0.1 * 4 * 16.5
            2,
            "The global discount is applied only on non discounted products",
        )

        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")
        self.assertEqual(lines[0].name, "Discounted Large Cabinet")
        self.assertAlmostEqual(lines[0].price_total, 160.0)
        self.assertEqual(lines[1].name, "Conference chair")
        self.assertAlmostEqual(lines[1].price_total, 66.0)
        self.assertIn("Discount: 10%", lines[2].name)
        self.assertAlmostEqual(lines[2].price_total, -6.6)

    def test_program_skip_discounted_products_filter_programs(self):
        order = self.empty_order
        self.global_promo.skip_discounted_products = True
        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Discounted Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
                "discount": 50.0,
            }
        )
        self.assertEquals(
            len(order._get_applicable_programs()),
            0,
            "No program should be applicable",
        )
        sol = self.env["sale.order.line"].create(
            {
                "product_id": self.conferenceChair.id,
                "name": "Conference chair",
                "product_uom_qty": 4.0,
                "order_id": order.id,
            }
        )
        self.assertEquals(
            order._get_applicable_programs(),
            self.global_promo,
            "The program is now applicable",
        )
        sol.unlink()
        self.assertEquals(
            len(order._get_applicable_programs()),
            0,
            "No program should be applicable",
        )

    def test_program_skip_discounted_products_new_discount(self):
        order = self.empty_order
        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Discounted Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
            }
        )
        chair = self.env["sale.order.line"].create(
            {
                "product_id": self.conferenceChair.id,
                "name": "Conference chair",
                "product_uom_qty": 4.0,
                "order_id": order.id,
            }
        )

        self.assertEqual(
            order.amount_total,
            386.0,  # 320 + 4 * 16.5
            "Before computing promotions, total should be the sum of product price.",
        )

        self.global_promo.skip_discounted_products = True
        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            347.4,  # 386 - 0.1 * 386
            2,
            "The global discount is applied",
        )

        chair.discount = 75
        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            304.5,  # 320 + 4 * 16.5 * 0.25 - 0.1 * 320
            2,
            "The global discount is applied only on non discounted products",
        )

    def test_program_skip_discounted_products_best_offer(self):
        order = self.empty_order
        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Discounted Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
                "discount": 20.0,
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": self.conferenceChair.id,
                "name": "Conference chair",
                "product_uom_qty": 4.0,
                "order_id": order.id,
                "discount": 20.0,
            }
        )

        self.assertEqual(
            order.amount_total,
            308.8,  # 320 * 0.8 + 4 * 16.5 * 0.8
            "Before computing promotions, total should be the sum of product price.",
        )

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            277.92,  # 308.8 - 0.1 * 308.8
            2,
            "The global discount is applied",
        )

        self.env["coupon.program"].create(
            {
                "name": "25% incredible offer",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 25.0,
                "program_type": "promotion_program",
                "sequence": 30,
                "skip_discounted_products": True,
            }
        )
        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            277.92,  # 308.8 - 0.1 * 308.8
            2,
            "The old global discount is still applied even though the new "
            "one is better on non discounted products",
        )

    def test_program_skip_discounted_products_with_coupon(self):
        order = self.empty_order
        self.global_promo.skip_discounted_products = True
        self.global_promo.promo_code_usage = "code_needed"
        self.global_promo.program_type = "coupon_program"
        self.env["coupon.generate.wizard"].with_context(
            active_id=self.global_promo.id
        ).create({}).generate_coupon()
        coupon = self.global_promo.coupon_ids[0]

        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Discounted Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
                "discount": 50.0,
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
            226.0,  # 320/2 + 4 * 16.5
            "Before computing promotions, total should be the sum of product price.",
        )
        order.recompute_coupon_lines()
        self.assertEqual(
            order.amount_total,
            226.0,  # 320/2 + 4 * 16.5
            "Before computing promotions, total should be the sum of product price.",
        )
        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": coupon.code}
        ).process_coupon()
        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            219.4,  # 226 - 0.1 * 4 * 16.5
            2,
            "The global discount is applied only on non discounted products",
        )

        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")
        self.assertEqual(lines[0].name, "Discounted Large Cabinet")
        self.assertAlmostEqual(lines[0].price_total, 160.0)
        self.assertEqual(lines[1].name, "Conference chair")
        self.assertAlmostEqual(lines[1].price_total, 66.0)
        self.assertIn("Discount: 10%", lines[2].name)
        self.assertAlmostEqual(lines[2].price_total, -6.6)

    def test_program_skip_discounted_products_with_coupon_unapplicable(self):
        order = self.empty_order
        self.global_promo.skip_discounted_products = True
        self.global_promo.promo_code_usage = "code_needed"
        self.global_promo.program_type = "coupon_program"
        self.env["coupon.generate.wizard"].with_context(
            active_id=self.global_promo.id
        ).create({}).generate_coupon()
        coupon = self.global_promo.coupon_ids[0]

        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Discounted Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
                "discount": 50.0,
            }
        )

        self.assertEqual(
            order.amount_total,
            160.0,  # 320/2
            "Before computing promotions, total should be the sum of product price.",
        )
        order.recompute_coupon_lines()
        self.assertEqual(
            order.amount_total,
            160.0,  # 320/2
            "Before computing promotions, total should be the sum of product price.",
        )

        with self.assertRaises(UserError) as error:
            self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
                {"coupon_code": coupon.code}
            ).process_coupon()
        self.assertEqual(
            error.exception.name,
            "The coupon code can't be applied on discounted products.",
        )

    def test_program_skip_discounted_products_with_coupon_unapplicable_other_error(
        self,
    ):
        order = self.empty_order
        self.global_promo.promo_code_usage = "code_needed"
        self.global_promo.program_type = "coupon_program"
        self.global_promo.rule_min_quantity = 2
        self.env["coupon.generate.wizard"].with_context(
            active_id=self.global_promo.id
        ).create({}).generate_coupon()
        coupon = self.global_promo.coupon_ids[0]

        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Discounted Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
                "discount": 50.0,
            }
        )

        with self.assertRaises(UserError) as error:
            self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
                {"coupon_code": coupon.code}
            ).process_coupon()
        self.assertEqual(
            error.exception.name,
            "You don't have the required product quantities on your sales order. "
            "All the products should be recorded on the sales order. "
            "(Example: You need to have 3 T-shirts on your sales order if "
            "the promotion is 'Buy 2, Get 1 Free').",
        )

    def test_program_skip_discounted_products_with_coupon_unapplicable_as_program(self):
        order = self.empty_order
        self.global_promo.skip_discounted_products = True
        self.global_promo.promo_code_usage = "code_needed"
        self.global_promo.promo_code = "THECODE"

        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Discounted Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
                "discount": 50.0,
            }
        )

        self.assertEqual(
            order.amount_total,
            160.0,  # 320/2
            "Before computing promotions, total should be the sum of product price.",
        )
        order.recompute_coupon_lines()
        self.assertEqual(
            order.amount_total,
            160.0,  # 320/2
            "Before computing promotions, total should be the sum of product price.",
        )

        with self.assertRaises(UserError) as error:
            self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
                {"coupon_code": "THECODE"}
            ).process_coupon()
        self.assertEqual(
            error.exception.name,
            "The coupon code can't be applied on discounted products.",
        )

    def test_program_skip_discounted_products_with_coupon_remove_last_coupon_relevant_line(
        self,
    ):
        order = self.empty_order
        self.global_promo.skip_discounted_products = True
        self.global_promo.promo_code_usage = "code_needed"
        self.global_promo.program_type = "coupon_program"
        self.env["coupon.generate.wizard"].with_context(
            active_id=self.global_promo.id
        ).create({}).generate_coupon()
        coupon = self.global_promo.coupon_ids[0]

        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Discounted Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
                "discount": 50.0,
            }
        )

        sol = self.env["sale.order.line"].create(
            {
                "product_id": self.conferenceChair.id,
                "name": "Conference chair",
                "product_uom_qty": 4.0,
                "order_id": order.id,
            }
        )
        self.assertEqual(
            order.amount_total,
            226.0,  # 320/2 + 4 * 16.5
            "Before computing promotions, total should be the sum of product price.",
        )
        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": coupon.code}
        ).process_coupon()
        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            219.4,  # 226 - 0.1 * 4 * 16.5
            2,
            "The global discount is applied only on non discounted products",
        )

        sol.unlink()
        order.recompute_coupon_lines()

        self.assertEqual(
            order.amount_total,
            160.0,  # 320/2
            "Coupon should not be applied anymore.",
        )

        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 line.")
        self.assertEqual(lines[0].name, "Discounted Large Cabinet")
        self.assertAlmostEqual(lines[0].price_total, 160.0)
