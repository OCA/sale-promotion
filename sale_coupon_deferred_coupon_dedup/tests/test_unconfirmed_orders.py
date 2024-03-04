# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.sale_coupon.tests.common import TestSaleCouponCommon


@tagged("post_install", "-at_install")
class TestSaleCouponUnconfirmedOrders(TestSaleCouponCommon):
    def setUp(self):
        super(TestSaleCouponUnconfirmedOrders, self).setUp()

        self.drawerBlack = self.env["product.product"].create(
            {
                "name": "Drawer Black",
                "list_price": 25.0,
                "taxes_id": False,
            }
        )

        self.partner = self.env["res.partner"].create(
            {
                "name": "Steve Bucknor",
                "email": "steve.bucknor@example.com",
            }
        )

        self.coupon_program = self.env["coupon.program"].create(
            {
                "name": "$5 coupon",
                "program_type": "coupon_program",
                "reward_type": "discount",
                "discount_type": "fixed_amount",
                "discount_fixed_amount": 5,
                "active": True,
                "discount_apply_on": "on_order",
            }
        )

    def test_unconfirmed_orders_same_coupon_add(self):
        # Let's create 2 new orders
        order = self.env["sale.order"].create(
            {"state": "draft", "partner_id": self.partner.id}
        )
        order2 = self.env["sale.order"].create(
            {"state": "sent", "partner_id": self.partner.id}
        )

        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "drawer black",
                "product_uom_qty": 4.0,
                "order_id": order.id,
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "drawer black",
                "product_uom_qty": 4.0,
                "order_id": order2.id,
            }
        )

        self.assertEqual(order.amount_total, 100)
        self.assertEqual(order2.amount_total, 100)

        self.env["coupon.generate.wizard"].with_context(
            active_id=self.coupon_program.id
        ).create(
            {
                "generation_type": "nbr_coupon",
                "nbr_coupons": 1,
            }
        ).generate_coupon()

        # Since orders are not confirmed, both should be able to get this coupon
        coupon = self.coupon_program.coupon_ids
        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": coupon.code}
        ).process_coupon()
        order.recompute_coupon_lines()

        self.env["sale.coupon.apply.code"].with_context(active_id=order2.id).create(
            {"coupon_code": coupon.code}
        ).process_coupon()
        order2.recompute_coupon_lines()

        self.assertEqual(order.amount_total, 95)
        self.assertEqual(order2.amount_total, 95)

        # The coupon should still be valid
        self.assertEqual(coupon.state, "new")

    def test_confirmed_orders_same_coupon_not_add(self):
        # Let's create confirmed orders
        order = self.env["sale.order"].create(
            {"state": "sale", "partner_id": self.partner.id}
        )
        order2 = self.env["sale.order"].create(
            {"state": "done", "partner_id": self.partner.id}
        )

        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "drawer black",
                "product_uom_qty": 4.0,
                "order_id": order.id,
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "drawer black",
                "product_uom_qty": 4.0,
                "order_id": order2.id,
            }
        )

        self.env["coupon.generate.wizard"].with_context(
            active_id=self.coupon_program.id
        ).create(
            {
                "generation_type": "nbr_coupon",
                "nbr_coupons": 1,
            }
        ).generate_coupon()

        # Since orders are not confirmed, both should be able to get this coupon
        coupon = self.coupon_program.coupon_ids
        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": coupon.code}
        ).process_coupon()
        order.recompute_coupon_lines()

        with self.assertRaises(UserError) as error:
            self.env["sale.coupon.apply.code"].with_context(active_id=order2.id).create(
                {"coupon_code": coupon.code}
            ).process_coupon()

        self.assertIn("This coupon has already been used", str(error.exception))

        self.assertEqual(order.amount_total, 95)
        self.assertEqual(order2.amount_total, 100)

        # The coupon shouldn't be valid anymore
        self.assertEqual(coupon.state, "used")

    def test_unconfirmed_orders_same_coupon_add_then_confirm_one(self):
        # Let's create 2 new orders
        order = self.env["sale.order"].create(
            {"state": "draft", "partner_id": self.partner.id}
        )
        order2 = self.env["sale.order"].create(
            {"state": "sent", "partner_id": self.partner.id}
        )

        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "drawer black",
                "product_uom_qty": 4.0,
                "order_id": order.id,
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "drawer black",
                "product_uom_qty": 4.0,
                "order_id": order2.id,
            }
        )

        self.env["coupon.generate.wizard"].with_context(
            active_id=self.coupon_program.id
        ).create(
            {
                "generation_type": "nbr_coupon",
                "nbr_coupons": 1,
            }
        ).generate_coupon()

        # Since orders are not confirmed, both should be able to get this coupon
        coupon = self.coupon_program.coupon_ids
        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": coupon.code}
        ).process_coupon()
        order.recompute_coupon_lines()

        self.env["sale.coupon.apply.code"].with_context(active_id=order2.id).create(
            {"coupon_code": coupon.code}
        ).process_coupon()
        order2.recompute_coupon_lines()

        # Now let's confirm an order
        order.action_confirm()
        self.assertEqual(len(order.unconfirmed_applied_coupon_ids), 0)

        # The other shouldn't be able to be confirmed since its coupon
        # is not valid anymore

        with self.assertRaises(UserError) as error:
            order2.action_confirm()
        self.assertIn("This coupon has already been used", str(error.exception))

    def test_unconfirmed_orders_coupon_removal(self):
        # Let's create a new order
        order = self.env["sale.order"].create(
            {"state": "draft", "partner_id": self.partner.id}
        )

        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "drawer black",
                "product_uom_qty": 4.0,
                "order_id": order.id,
            }
        )

        self.assertEqual(order.amount_total, 100)

        # Add it a unconfirmed coupon
        self.env["coupon.generate.wizard"].with_context(
            active_id=self.coupon_program.id
        ).create(
            {
                "generation_type": "nbr_coupon",
                "nbr_coupons": 1,
            }
        ).generate_coupon()

        coupon = self.coupon_program.coupon_ids
        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": coupon.code}
        ).process_coupon()
        order.recompute_coupon_lines()

        self.assertEqual(order.amount_total, 95)
        # Now remove it
        order.order_line.filtered(lambda x: "$5 coupon" in x.name).unlink()

        order.recompute_coupon_lines()
        self.assertEqual(order.amount_total, 100)

    def test_unconfirmed_orders_same_coupon_added_only_once(self):
        order = self.env["sale.order"].create(
            {"state": "draft", "partner_id": self.partner.id}
        )

        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "drawer black",
                "product_uom_qty": 4.0,
                "order_id": order.id,
            }
        )

        self.env["coupon.generate.wizard"].with_context(
            active_id=self.coupon_program.id
        ).create(
            {
                "generation_type": "nbr_coupon",
                "nbr_coupons": 1,
            }
        ).generate_coupon()

        # Since orders are not confirmed, both should be able to get this coupon
        coupon = self.coupon_program.coupon_ids
        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": coupon.code}
        ).process_coupon()
        order.recompute_coupon_lines()

        with self.assertRaises(UserError) as error:
            self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
                {"coupon_code": coupon.code}
            ).process_coupon()

        self.assertIn(
            "This coupon has already been used in this order", str(error.exception)
        )

    def test_unconfirmed_orders_same_coupon_program_added_only_once(self):
        order = self.env["sale.order"].create(
            {"state": "draft", "partner_id": self.partner.id}
        )

        self.env["sale.order.line"].create(
            {
                "product_id": self.drawerBlack.id,
                "name": "drawer black",
                "product_uom_qty": 4.0,
                "order_id": order.id,
            }
        )

        self.env["coupon.generate.wizard"].with_context(
            active_id=self.coupon_program.id
        ).create(
            {
                "generation_type": "nbr_coupon",
                "nbr_coupons": 2,
            }
        ).generate_coupon()

        # we should be able to add only one coupon of the same program
        coupons = (x for x in self.coupon_program.coupon_ids)

        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": next(coupons).code}
        ).process_coupon()

        with self.assertRaises(UserError) as error:
            self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
                {"coupon_code": next(coupons).code}
            ).process_coupon()

        self.assertIn(
            "A Coupon is already applied for the same reward", str(error.exception)
        )
