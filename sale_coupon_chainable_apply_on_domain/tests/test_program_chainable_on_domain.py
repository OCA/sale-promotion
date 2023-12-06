# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import tagged

from odoo.addons.sale_coupon.tests.common import TestSaleCouponCommon


@tagged("post_install", "-at_install")
class TestSaleCouponChainableApplyOnDomain(TestSaleCouponCommon):
    def setUp(self):
        super(TestSaleCouponChainableApplyOnDomain, self).setUp()

        self.largeCabinet = self.env["product.product"].create(
            {
                "name": "Large Cabinet",
                "list_price": 320.0,
                "taxes_id": False,
            }
        )
        self.pedalBin = self.env["product.product"].create(
            {
                "name": "Pedal Bin",
                "list_price": 47.0,
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

        self.largeMeetingTable = self.env["product.product"].create(
            {
                "name": "Large Meeting Table",
                "list_price": 40000.0,
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

        self.all_products_promo = self.env["coupon.program"].create(
            {
                "name": "10% on all products",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 10.0,
                "program_type": "promotion_program",
                "sequence": 20,
                "discount_apply_on": "product_domain",
                "discount_product_domain": '[["name","ilike","c"]]',
            }
        )

    def test_program_chainable(self):
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
            "Before computing promotions, total should be the sum of products prices.",
        )

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            347.4,  # 386 - 0.1 * 386
            2,
            "The global discount is applied",
        )

        self.env["coupon.program"].create(
            {
                "name": "50% incredible offer",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 50.0,
                "program_type": "promotion_program",
                "sequence": 30,
                "discount_apply_on": "product_domain",
                "discount_product_domain": '[["name","ilike","c"]]',
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
            135.1,  # 386 - 0.1 * 386 - 0.5 * 386 - 0.05 * 386
            2,
            "All discounts apply independently",
        )

        program.chainable = True
        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            146.68,  # 386 - 0.1 * 386 - 0.5 * 386 - 0.05 * (386 - 0.1 * 386 - 0.5 * 386)
            2,
            "The global discount is now chained on the chainable discount",
        )

    def test_program_chainable_order(self):
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

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            347.4,  # 386 - 0.1 * 386
            2,
            "The global discount is applied",
        )

        program = self.env["coupon.program"].create(
            {
                "name": "5% with prime program",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 5.0,
                "program_type": "promotion_program",
                "sequence": 30,  # Comes after 10%
                "chainable": True,
            }
        )
        order.recompute_coupon_lines()
        lines = list(order.order_line)
        self.assertEqual(len(lines), 4, "Order should have 4 lines.")
        self.assertEqual(lines[0].name, "Large Cabinet")
        self.assertAlmostEqual(lines[0].price_total, 320.0)
        self.assertEqual(lines[1].name, "Conference chair")
        self.assertAlmostEqual(lines[1].price_total, 66.0)
        self.assertIn("Discount: 10%", lines[2].name)
        self.assertAlmostEqual(lines[2].price_total, -38.6)
        self.assertIn("Discount: 5%", lines[3].name)
        self.assertAlmostEqual(lines[3].price_total, -17.37)

        self.assertAlmostEqual(
            order.amount_total,
            330.03,  # 386 - 0.1 * 386 - 0.05 * (386 - 0.1 * 386)
            2,
            "The global discount is chained on the chainable discount in the right order",
        )

        order._get_reward_lines().unlink()
        program.sequence = 1  # Now comes first

        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 4, "Order should have 4 lines.")
        self.assertEqual(lines[0].name, "Large Cabinet")
        self.assertAlmostEqual(lines[0].price_total, 320.0)
        self.assertEqual(lines[1].name, "Conference chair")
        self.assertAlmostEqual(lines[1].price_total, 66.0)
        self.assertIn("Discount: 5%", lines[2].name)
        self.assertAlmostEqual(lines[2].price_total, -19.3)
        self.assertIn("Discount: 10%", lines[3].name)
        self.assertAlmostEqual(
            lines[3].price_total, -38.6
        )  # 38.6 since it's not chainable

        self.assertAlmostEqual(
            order.amount_total,
            328.1,  # 386 - 0.05 * 386 - 0.1 * 386
            2,
            "The global discount is chained on the chainable discount in the new order",
        )
        self.all_products_promo.chainable = True
        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 4, "Order should have 4 lines.")
        self.assertEqual(lines[0].name, "Large Cabinet")
        self.assertAlmostEqual(lines[0].price_total, 320.0)
        self.assertEqual(lines[1].name, "Conference chair")
        self.assertAlmostEqual(lines[1].price_total, 66.0)
        self.assertIn("Discount: 5%", lines[2].name)
        self.assertAlmostEqual(lines[2].price_total, -19.3)
        self.assertIn("Discount: 10%", lines[3].name)
        self.assertAlmostEqual(lines[3].price_total, -36.67)

        self.assertAlmostEqual(
            order.amount_total,
            330.03,  # 386 - 0.05 * 386 - 0.1 * (386 - 0.05 * 386)
            2,
            "The global discount is now chainable so the total is higher",
        )

    def test_program_chainable_with_non_global_program(self):
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
                "name": "1 Product F = 5$ discount",
                "promo_code_usage": "no_code_needed",
                "reward_type": "discount",
                "discount_type": "fixed_amount",
                "discount_fixed_amount": 5,
                "sequence": 80,
            }
        )

        self.env["coupon.program"].create(
            {
                "name": "7% reduction on Large Cabinet in cart",
                "promo_code_usage": "no_code_needed",
                "reward_type": "discount",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 7.0,
                "discount_apply_on": "product_domain",
                "discount_product_domain": '[["name","ilike","cabinet"]]',
                "sequence": 90,
            }
        )

        self.env["coupon.program"].create(
            {
                "name": "20% reduction on cheapest",
                "promo_code_usage": "no_code_needed",
                "reward_type": "discount",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 20.0,
                "discount_apply_on": "cheapest_product",
                "sequence": 100,
            }
        )

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            316.7,  # 386 - 0.1 * 386 - 5 - 0.07 * 320 - 0.2 * 16.5
            2,
            "All the promotions should be taken in account",
        )

        self.env["coupon.program"].create(
            {
                "name": "5% with prime program",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 5.0,
                "program_type": "promotion_program",
                "sequence": 500,  # Comes after 10%
                "chainable": True,
            }
        )
        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            # 386 - 0.1 * 386 - 5 - 0.07 * 320 - 0.2 * 16.5
            # - 0.05 * (386 - 0.1 * 386 - 5 - 0.07 * 320 - 0.2 * 16.5)
            300.865,
            2,
            "All the previous promotions and the chainable are applied in the right order",
        )

    def test_program_chainable_fixed_global_discount_first(self):
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
                "name": "50$ discount",
                "promo_code_usage": "no_code_needed",
                "reward_type": "discount",
                "discount_type": "fixed_amount",
                "discount_fixed_amount": 50,
                "sequence": 20,
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
                "chainable": True,
            }
        )

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            282.53,  # 386 - 0.1 * 386 - 50 - 0.05 * (386 - 0.1 * 386 - 50)
            2,
            "Chainable promo should apply on fixed amount discount.",
        )

    def test_program_chainable_fixed_global_discount_last(self):
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
                "name": "50$ discount",
                "promo_code_usage": "no_code_needed",
                "reward_type": "discount",
                "discount_type": "fixed_amount",
                "discount_fixed_amount": 50,
                "sequence": 100,
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
                "chainable": True,
            }
        )

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            280.03,  # 386 - 0.1 * 386 - 0.05 * (386 - 0.1 * 386) - 50
            2,
            "Chainable promo should apply on fixed amount discount.",
        )

    def test_program_chainable_multi_discounts(self):
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
                "name": "20% prime first",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 20.0,
                "program_type": "promotion_program",
                "sequence": 1,
                "chainable": True,
                "discount_apply_on": "product_domain",
                "discount_product_domain": '[["name","ilike","C"]]',
            }
        )

        # In order we have the non chainable 10% here

        self.env["coupon.program"].create(
            {
                "name": "30% prime second",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 30.0,
                "program_type": "promotion_program",
                "sequence": 30,
                "chainable": True,
            }
        )

        self.env["coupon.program"].create(
            {
                "name": "11% non chainable",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 11.0,
                "program_type": "promotion_program",
                "sequence": 40,
                "discount_apply_on": "product_domain",
                "discount_product_domain": '[["name","ilike","C"]]',
            }
        )
        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            146.68,  # 386 - 0.2 * 386 - 0.1 * 386 - 0.3 * (386 - 0.1 * 386 - 0.2 * 386) - 0.11 * 386  # noqa
            2,
            "Chainable promo should chain, other non chainable should apply on full total.",
        )

    def test_program_chainable_varying_taxes(self):
        order = self.empty_order
        high_tax = self.env["account.tax"].create(
            {
                "name": "25% Tax",
                "amount_type": "percent",
                "amount": 25,
                "price_include": True,
            }
        )
        low_tax = self.env["account.tax"].create(
            {
                "name": "10% Tax",
                "amount_type": "percent",
                "amount": 10,
                "price_include": True,
            }
        )

        self.largeCabinet.taxes_id = high_tax
        self.conferenceChair.taxes_id = low_tax
        self.drawerBlack.taxes_id = False

        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "High Tax Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": self.conferenceChair.id,
                "name": "Low Tax Conference chair",
                "product_uom_qty": 4.0,
                "order_id": order.id,
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "Untaxed Drawer Black",
                "product_uom_qty": 2.0,
                "order_id": order.id,
            }
        )
        self.env["coupon.program"].create(
            {
                "name": "5% with prime program",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 5.0,
                "program_type": "promotion_program",
                "sequence": 30,  # Comes after 10%
                "chainable": True,
            }
        )
        self.assertAlmostEqual(
            order.amount_untaxed,
            366.0,  # 320 / 1.25 + 16.5 * 4 / 1.1 + 25 * 2
            2,
            "Untaxed amount should be 366",
        )
        self.assertAlmostEqual(
            order.amount_total,
            436.0,  # 320 + 16.5 * 4 + 25 * 2
            2,
            "Taxes should apply, taxed total should be 436",
        )
        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 9, "Order should have 9 lines.")
        self.assertEqual(lines[0].name, "High Tax Large Cabinet")
        self.assertAlmostEqual(lines[0].price_subtotal, 256.0)
        self.assertAlmostEqual(lines[0].price_total, 320.0)
        self.assertEqual(lines[1].name, "Low Tax Conference chair")
        self.assertAlmostEqual(lines[1].price_subtotal, 60.0)
        self.assertAlmostEqual(lines[1].price_total, 66.0)
        self.assertEqual(lines[2].name, "Untaxed Drawer Black")
        self.assertAlmostEqual(lines[2].price_subtotal, 50.0)
        self.assertAlmostEqual(lines[2].price_total, 50.0)
        self.assertIn("Discount: 10%", lines[3].name)
        self.assertIn("25% Tax", lines[3].name)
        self.assertAlmostEqual(lines[3].price_subtotal, -25.6)
        self.assertAlmostEqual(lines[3].price_total, -32.0)
        self.assertIn("Discount: 10%", lines[4].name)
        self.assertIn("10% Tax", lines[4].name)
        self.assertAlmostEqual(lines[4].price_subtotal, -6.0)
        self.assertAlmostEqual(lines[4].price_total, -6.6)

        self.assertIn("Discount: 10%", lines[5].name)
        self.assertAlmostEqual(lines[5].price_subtotal, -5.0)
        self.assertAlmostEqual(lines[5].price_total, -5.0)

        self.assertIn("Discount: 5%", lines[6].name)
        self.assertIn("25% Tax", lines[6].name)
        self.assertAlmostEqual(
            lines[6].price_subtotal, -11.52
        )  # - 0.05 * (256 - 0.1 * 256)
        self.assertAlmostEqual(
            lines[6].price_total, -14.4
        )  # - 0.05 * (320 - 0.1 * 320)

        self.assertIn("Discount: 5%", lines[7].name)
        self.assertIn("10% Tax", lines[7].name)
        self.assertAlmostEqual(
            lines[7].price_subtotal, -2.7
        )  # - 0.05 * (60 - 0.1 * 60)
        self.assertAlmostEqual(lines[7].price_total, -2.97)  # - 0.05 * (66 - 0.1 * 66)
        self.assertIn("Discount: 5%", lines[8].name)
        self.assertAlmostEqual(lines[8].price_subtotal, -2.25)
        self.assertAlmostEqual(lines[8].price_total, -2.25)

        self.assertAlmostEqual(
            order.amount_untaxed,
            312.93,  # 366 - (366 * 0.1) - 0.05 * (366 - (366 * 0.1))
            2,
            "Untaxed discount amount should be 329.40",
        )
        self.assertAlmostEqual(
            order.amount_total,
            372.78,  # 436 - (436 * 0.1) - 0.05 * (436 - (436 * 0.1))
            2,
            "Taxes should apply, taxed total should be 392.40",
        )

    def test_program_chainable_free_product_coupon(self):
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
                "chainable": True,
            }
        )
        coupon_program = self.env["coupon.program"].create(
            {
                "name": "2 free conference chair if at least 1 large cabinet",
                "promo_code_usage": "code_needed",
                "program_type": "promotion_program",
                "reward_type": "product",
                "reward_product_quantity": 2,
                "reward_product_id": self.conferenceChair.id,
                "rule_min_quantity": 1,
                "rule_products_domain": '["&", ["sale_ok","=",True], '
                '["name","ilike","large cabinet"]]',
                "sequence": 1,
            }
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
            # 386 - 2 * 16.5 - 0.1 * (386 - 2 * 16.5)
            # - 0.05 * (386 - 2 * 16.5 - 0.1 * (386 - 2 * 16.5))
            301.815,
            2,
            "Chainable promo should apply on fixed amount discount.",
        )

    def test_program_chainable_global_discount_coupon(self):
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
                "chainable": True,
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
                "discount_apply_on": "product_domain",
                "discount_product_domain": '[["name","ilike","C"]]',
            }
        )
        self.all_products_promo.active = False

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
            183.35,  # 386 - 0.5 * 386 - 0.05 * (386 - 0.5 * 386)
            2,
            "Applied coupons should be taken in account.",
        )

    def test_program_chainable_on_various_specific_products(self):
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
                "product_id": self.pedalBin.id,
                "name": "Pedal Bin",
                "product_uom_qty": 10.0,
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
        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "Drawer Black",
                "product_uom_qty": 2.0,
                "order_id": order.id,
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": self.largeMeetingTable.id,
                "name": "Large Meeting Table",
                "product_uom_qty": 1.0,
                "order_id": order.id,
            }
        )
        # All promo will be chainable here
        self.all_products_promo.chainable = True

        self.assertEqual(
            order.amount_total,
            40906.00,  # 320 + 10 * 47 + 4 * 16.5 + 2 * 25 + 40000
            "Before computing promotions, total should be the sum of products prices.",
        )
        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            40862.4,  # 40906.00 - 0.1 * (320 + 4 * 16.5 + 2 * 25)
            2,
            "The partial discount is applied",
        )

        # Add another specific products chainable discount
        self.env["coupon.program"].create(
            {
                "name": "5% on cabinet and pedal",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 5.0,
                "program_type": "promotion_program",
                "sequence": 0,
                "chainable": True,
                "discount_apply_on": "product_domain",
                "discount_product_domain": '[["name","ilike","bin"]]',
            }
        )
        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            #                                                      chain here
            40824.5,  # 40906.00 - 0.05 * (320 + 10 * 47) - 0.1 * ((320 - 0.05 * 320) + 4 * 16.5 + 2 * 25)  # noqa
            2,
            "Chainable specific products discount should only chain on common products",
        )

        # Add yet another specific products chainable discount
        self.env["coupon.program"].create(
            {
                "name": "7.5% on pedal and chairs",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 7.5,
                "program_type": "promotion_program",
                "sequence": 10,
                "chainable": True,
                "discount_apply_on": "specific_products",
                "discount_specific_product_ids": [
                    (
                        6,
                        0,
                        [
                            self.pedalBin.id,
                            self.conferenceChair.id,
                        ],
                    )
                ],
            }
        )
        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            40786.55,  # 40906.00 - 0.05 * (320 + 10 * 47) - 0.075 * ((10 * 47 - 0.05 * (10 * 47)) + 4 * 16.5) - 0.1 * ((320 - 0.05 * 320) + (4 * 16.5 - 0.075 * (4 * 16.5)) + 2 * 25)  # noqa
            2,
            "Chainable specific products discount should only chain on common products twice",
        )
        # Add a global discount
        self.env["coupon.program"].create(
            {
                "name": "15% on order",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 15.0,
                "program_type": "promotion_program",
                "sequence": 15,
                "chainable": True,
            }
        )
        self.all_products_promo.active = False
        order.recompute_coupon_lines()
        self.assertAlmostEqual(
            order.amount_total,
            34703.85,  # 40906.00 - 0.05 * (320 + 10 * 47) - 0.075 * ((10 * 47 - 0.05 * (10 * 47)) + 4 * 16.5) - 0.15 * (40906.00 - 0.05 * (320 + 10 * 47) - 0.075 * ((10 * 47 - 0.05 * (10 * 47)) + 4 * 16.5))  # noqa
            2,
            "Chainable specific products discount should chain on common products "
            "and on global discount",
        )

        self.all_products_promo.active = True
        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            34668.88,  # 40906.00 - 0.05 * (320 + 10 * 47) - 0.075 * ((10 * 47 - 0.05 * (10 * 47)) + 4 * 16.5) - 0.15 * (40906.00 - 0.05 * (320 + 10 * 47) - 0.075 * ((10 * 47 - 0.05 * (10 * 47)) + 4 * 16.5)) - 0.1 * ((320 - 0.05 * 320 - 0.15 * (320 - 0.05 * 320)) + 4 * 16.5 - 0.075 * (4 * 16.5) - 0.15 * (4 * 16.5 - 0.075 * (4 * 16.5)) + 2 * 25 - 0.15 * (2 * 25))  # noqa
            2,
            "Chainable specific products discount should chain twice on common "
            "products and on global discount",
        )
