# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.sale_coupon.tests.common import TestSaleCouponCommon


@tagged("post_install", "-at_install")
class TestSaleCouponAddFreeProducts(TestSaleCouponCommon):
    def setUp(self):
        super(TestSaleCouponAddFreeProducts, self).setUp()

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

        self.global_promo_with_product_rule = self.env["coupon.program"].create(
            {
                "name": "Buy 1 large cabinet, get a chair for free",
                "promo_code_usage": "no_code_needed",
                "reward_type": "product",
                "program_type": "promotion_program",
                "reward_product_id": self.conferenceChair.id,
                "rule_products_domain": '[["name","ilike","large cabinet"]]',
            }
        )

        self.global_promo_with_code = self.env["coupon.program"].create(
            {
                "name": "Get 1 large cabinet for free",
                "promo_code_usage": "code_needed",
                "promo_code": "FREE",
                "reward_type": "product",
                "program_type": "promotion_program",
                "reward_product_id": self.largeCabinet.id,
            }
        )

    def test_program_auto_add_free_products_for_coupon(self):
        order = self.empty_order

        self.global_promo_with_code.program_type = "coupon_program"

        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "Drawer Black",
                "product_uom_qty": 2.0,
                "order_id": order.id,
            }
        )

        self.env["coupon.generate.wizard"].with_context(
            active_id=self.global_promo_with_code.id
        ).create(
            {
                "generation_type": "nbr_coupon",
                "nbr_coupons": 1,
            }
        ).generate_coupon()
        coupon = self.global_promo_with_code.coupon_ids

        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 line.")

        with self.assertRaisesRegexp(
            UserError,
            "The reward products should be in the sales order lines to apply the discount.",
        ):
            self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
                {"coupon_code": coupon.code}
            ).process_coupon()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 line.")

        self.global_promo_with_code.auto_add_free_products = True

        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": coupon.code}
        ).process_coupon()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")
        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")

    def test_program_auto_remove_free_products_for_coupon(self):
        order = self.empty_order

        self.global_promo_with_code.program_type = "coupon_program"
        self.global_promo_with_code.auto_add_free_products = True

        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "Drawer Black",
                "product_uom_qty": 2.0,
                "order_id": order.id,
            }
        )

        self.env["coupon.generate.wizard"].with_context(
            active_id=self.global_promo_with_code.id
        ).create(
            {
                "generation_type": "nbr_coupon",
                "nbr_coupons": 1,
            }
        ).generate_coupon()
        coupon = self.global_promo_with_code.coupon_ids

        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": coupon.code}
        ).process_coupon()
        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")
        order.order_line.filtered(lambda x: "Free Product" in x.name).unlink()
        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 lines.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 2)

    def test_program_auto_add_free_products_for_promo_with_code(self):
        order = self.empty_order
        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "Drawer Black",
                "product_uom_qty": 2.0,
                "order_id": order.id,
            }
        )
        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 line.")

        with self.assertRaisesRegexp(
            UserError,
            "The reward products should be in the sales order lines to apply the discount.",
        ):
            self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
                {"coupon_code": "FREE"}
            ).process_coupon()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 line.")

        self.global_promo_with_code.auto_add_free_products = True

        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": "FREE"}
        ).process_coupon()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")
        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")

    def test_program_auto_remove_free_products_for_promo_with_code(self):
        order = self.empty_order
        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "Drawer Black",
                "product_uom_qty": 2.0,
                "order_id": order.id,
            }
        )
        self.global_promo_with_code.auto_add_free_products = True

        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": "FREE"}
        ).process_coupon()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")
        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")
        order.order_line.filtered(lambda x: "Free Product" in x.name).unlink()
        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 lines.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 2)

    def test_program_auto_add_free_products_for_promo(self):
        order = self.empty_order
        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
            }
        )

        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 line.")

        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 line.")

        self.global_promo_with_product_rule.auto_add_free_products = True

        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")

        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")

    def test_program_auto_remove_free_products_for_promo(self):
        order = self.empty_order
        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
            }
        )

        self.global_promo_with_product_rule.auto_add_free_products = True

        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")
        order.order_line.filtered(lambda x: "Free Product" in x.name).unlink()
        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 lines.")
        self.assertEqual(lines[0].name, "Large Cabinet")
        self.assertEqual(lines[0].product_uom_qty, 1)

    def test_program_auto_add_free_products_for_promo_other_product_min_quantity(
        self,
    ):
        order = self.empty_order

        sol = self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
            }
        )

        self.global_promo_with_product_rule.auto_add_free_products = True
        self.global_promo_with_product_rule.rule_min_quantity = 2
        self.global_promo_with_product_rule.reward_product_quantity = 3

        order.recompute_coupon_lines()
        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 line.")

        sol.product_uom_qty = 2

        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")
        self.assertEqual(lines[0].name, "Large Cabinet")
        self.assertEqual(lines[0].product_uom_qty, 2)
        self.assertEqual(lines[1].name, "Conference Chair")
        self.assertEqual(lines[1].product_uom_qty, 3)
        self.assertEqual(lines[2].name, "Free Product - Conference Chair")
        self.assertEqual(lines[2].product_uom_qty, 3)

    def test_program_auto_remove_free_products_for_promo_other_product_min_quantity(
        self,
    ):
        order = self.empty_order

        sol = self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
            }
        )

        self.global_promo_with_product_rule.auto_add_free_products = True
        self.global_promo_with_product_rule.rule_min_quantity = 2
        self.global_promo_with_product_rule.reward_product_quantity = 3

        order.recompute_coupon_lines()
        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 line.")

        sol.product_uom_qty = 2

        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")
        self.assertEqual(lines[0].name, "Large Cabinet")
        self.assertEqual(lines[0].product_uom_qty, 2)
        self.assertEqual(lines[1].name, "Conference Chair")
        self.assertEqual(lines[1].product_uom_qty, 3)
        self.assertEqual(lines[2].name, "Free Product - Conference Chair")
        self.assertEqual(lines[2].product_uom_qty, 3)

        order.order_line.filtered(lambda x: "Free Product" in x.name).unlink()
        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 lines.")
        self.assertEqual(lines[0].name, "Large Cabinet")
        self.assertEqual(lines[0].product_uom_qty, 2)

    def test_program_auto_add_free_products_with_same_product_rules_simple(self):
        order = self.empty_order

        sol = self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "Drawer Black",
                "product_uom_qty": 2.0,
                "order_id": order.id,
            }
        )

        self.env["coupon.program"].create(
            {
                "name": "Buy 3 drawers, get 1 for free",
                "promo_code_usage": "no_code_needed",
                "reward_type": "product",
                "program_type": "promotion_program",
                "reward_product_id": self.drawerBlack.id,
                "reward_product_quantity": 1,
                "rule_min_quantity": 3,
                "rule_products_domain": '[["sale_ok","=",True], ["id","=", %d]]'
                % self.drawerBlack.id,
                "auto_add_free_products": True,
            }
        )

        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 line.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 2)

        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 line.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 2)

        sol.product_uom_qty = 3
        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 2, "Order should have 2 lines.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 4)
        self.assertEqual(lines[1].name, "Free Product - Drawer Black")
        self.assertEqual(lines[1].product_uom_qty, 1)

    def test_program_auto_remove_free_products_with_same_product_rules_simple(self):
        order = self.empty_order

        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "Drawer Black",
                "product_uom_qty": 3.0,
                "order_id": order.id,
            }
        )

        self.env["coupon.program"].create(
            {
                "name": "Buy 3 drawers, get 1 for free",
                "promo_code_usage": "no_code_needed",
                "reward_type": "product",
                "program_type": "promotion_program",
                "reward_product_id": self.drawerBlack.id,
                "reward_product_quantity": 1,
                "rule_min_quantity": 3,
                "rule_products_domain": '[["sale_ok","=",True], ["id","=", %d]]'
                % self.drawerBlack.id,
                "auto_add_free_products": True,
            }
        )

        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 2, "Order should have 2 lines.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 4)
        self.assertEqual(lines[1].name, "Free Product - Drawer Black")
        self.assertEqual(lines[1].product_uom_qty, 1)

        order.order_line.filtered(lambda x: "Free Product" in x.name).unlink()
        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 lines.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 3)

    def test_program_auto_add_remove_free_products_with_same_product_rules(self):
        order = self.empty_order

        sol = self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "Drawer Black",
                "product_uom_qty": 3.0,
                "order_id": order.id,
            }
        )

        self.env["coupon.program"].create(
            {
                "name": "Buy 3 drawers, get 12 for free",
                "promo_code_usage": "no_code_needed",
                "reward_type": "product",
                "program_type": "promotion_program",
                "reward_product_id": self.drawerBlack.id,
                "reward_product_quantity": 12,
                "rule_min_quantity": 3,
                "rule_products_domain": '[["sale_ok","=",True], ["id","=", %d]]'
                % self.drawerBlack.id,
                "auto_add_free_products": True,
            }
        )

        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 line.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 3)

        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 2, "Order should have 2 lines.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 15)
        self.assertEqual(lines[1].name, "Free Product - Drawer Black")
        self.assertEqual(lines[1].product_uom_qty, 12)

        order.order_line.filtered(lambda x: "Free Product" in x.name).unlink()
        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 line.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 3)

        sol.product_uom_qty = 4

        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 2, "Order should have 2 lines.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 15)
        self.assertEqual(lines[1].name, "Free Product - Drawer Black")
        self.assertEqual(lines[1].product_uom_qty, 12)

        order.order_line.filtered(lambda x: "Free Product" in x.name).unlink()
        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 line.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 4)

        sol.product_uom_qty = 1

        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 lines.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 1)

        sol.product_uom_qty = 2

        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 lines.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 2)

    def test_program_auto_add_free_products_min_amount(self):
        order = self.empty_order

        self.env["coupon.program"].create(
            {
                "name": "Buy a chair and 100$ get 2 drawers",
                "promo_code_usage": "no_code_needed",
                "reward_type": "product",
                "program_type": "promotion_program",
                "reward_product_id": self.drawerBlack.id,
                "rule_products_domain": '[["name","ilike","chair"]]',
                "rule_minimum_amount": 100.00,
                "reward_product_quantity": 2,
                "auto_add_free_products": True,
            }
        )

        sol = self.env["sale.order.line"].create(
            {
                "product_id": self.conferenceChair.id,
                "name": "Chair",
                "product_uom_qty": 6.0,
                "order_id": order.id,
            }
        )

        order.recompute_coupon_lines()
        self.assertEqual(order.amount_total, 99)
        # Amount is below rule_minimum_amount -> no free product
        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 lines.")

        sol.product_uom_qty = 7
        order.recompute_coupon_lines()
        # Amount is above rule_minimum_amount -> free product
        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")
        self.assertEqual(lines[0].name, "Chair")
        self.assertEqual(lines[0].product_uom_qty, 7)
        self.assertEqual(lines[1].name, "Drawer Black")
        self.assertEqual(lines[1].product_uom_qty, 2)
        self.assertEqual(lines[2].name, "Free Product - Drawer Black")
        self.assertEqual(lines[2].product_uom_qty, 2)

    def test_program_auto_add_free_products_for_promo_on_empty_cart(self):
        order = self.empty_order

        program = self.env["coupon.program"].create(
            {
                "name": "Get 1 drawer for free",
                "promo_code_usage": "no_code_needed",
                "reward_type": "product",
                "program_type": "promotion_program",
                "reward_product_id": self.drawerBlack.id,
                "auto_add_free_products": True,
            }
        )
        order.recompute_coupon_lines()
        lines = list(order.order_line)
        self.assertEqual(len(lines), 0, "Order should have no line.")

        program.always_reward_product = True

        order.recompute_coupon_lines()
        lines = list(order.order_line)
        self.assertEqual(len(lines), 2, "Order should have 2 lines.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 1)
        self.assertEqual(lines[1].name, "Free Product - Drawer Black")
        self.assertEqual(lines[1].product_uom_qty, 1)

        order.recompute_coupon_lines()
        self.assertEqual(len(lines), 2, "Order should have 2 lines.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 1)
        self.assertEqual(lines[1].name, "Free Product - Drawer Black")
        self.assertEqual(lines[1].product_uom_qty, 1)

        order.order_line.filtered(lambda x: "Free Product" in x.name).unlink()
        lines = list(order.order_line)
        self.assertEqual(len(lines), 0, "Order should have no line.")

    def test_program_auto_add_free_products_for_coupon_on_empty_cart(self):
        order = self.empty_order

        self.global_promo_with_code.program_type = "coupon_program"
        self.global_promo_with_code.auto_add_free_products = True

        self.env["coupon.generate.wizard"].with_context(
            active_id=self.global_promo_with_code.id
        ).create(
            {
                "generation_type": "nbr_coupon",
                "nbr_coupons": 1,
            }
        ).generate_coupon()
        coupon = self.global_promo_with_code.coupon_ids

        with self.assertRaisesRegexp(
            UserError,
            "The reward products should be in the sales order lines to apply the discount.",
        ):
            self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
                {"coupon_code": coupon.code}
            ).process_coupon()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 0, "Order should have no line.")

        self.global_promo_with_code.always_reward_product = True

        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": coupon.code}
        ).process_coupon()
        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 2, "Order should have 2 lines.")
        self.assertEqual(lines[0].name, "Large Cabinet")
        self.assertEqual(lines[0].product_uom_qty, 1)
        self.assertEqual(lines[1].name, "Free Product - Large Cabinet")
        self.assertEqual(lines[1].product_uom_qty, 1)

    def test_program_auto_add_free_products_for_promo_with_always_reward_product(self):
        order = self.empty_order

        self.env["coupon.program"].create(
            {
                "name": "Get 1 drawer for free",
                "promo_code_usage": "no_code_needed",
                "reward_type": "product",
                "program_type": "promotion_program",
                "reward_product_id": self.drawerBlack.id,
                "auto_add_free_products": True,
                "always_reward_product": True,
            }
        )

        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "Drawer Black",
                "product_uom_qty": 1.0,
                "order_id": order.id,
            }
        )
        order.recompute_coupon_lines()
        lines = list(order.order_line)
        self.assertEqual(len(lines), 2, "Order should have 2 lines.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 1)
        self.assertEqual(lines[1].name, "Free Product - Drawer Black")
        self.assertEqual(lines[1].product_uom_qty, 1)

        order.recompute_coupon_lines()
        self.assertEqual(len(lines), 2, "Order should have 2 lines.")
        self.assertEqual(lines[0].name, "Drawer Black")
        self.assertEqual(lines[0].product_uom_qty, 1)
        self.assertEqual(lines[1].name, "Free Product - Drawer Black")
        self.assertEqual(lines[1].product_uom_qty, 1)

    def test_program_auto_remove_free_products_for_promo_when_removing_condition_product(
        self,
    ):
        self.global_promo_with_product_rule.auto_add_free_products = True
        order = self.empty_order
        sol = self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
            }
        )

        lines = list(order.order_line)
        self.assertEqual(len(lines), 1, "Order should have 1 line.")

        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 3, "Order should have 3 lines.")

        sol.unlink()
        order.recompute_coupon_lines()

        lines = list(order.order_line)
        self.assertEqual(len(lines), 0, "Order should have no line.")
