# Copyright 2022 Ooops404
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import SavepointCase


@tagged("post_install", "-at_install")
class CetmixTestSaleCouponProgram(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.largeCabinet = cls.env["product.product"].create(
            {
                "name": "Large Cabinet",
                "list_price": 50.0,
                "taxes_id": False,
            }
        )
        cls.conferenceChair = cls.env["product.product"].create(
            {
                "name": "Conference Chair",
                "list_price": 100,
                "taxes_id": False,
            }
        )
        cls.pedalBin = cls.env["product.product"].create(
            {
                "name": "Pedal Bin",
                "list_price": 150,
                "taxes_id": False,
            }
        )
        cls.drawerBlack = cls.env["product.product"].create(
            {
                "name": "Drawer Black",
                "list_price": 200,
                "taxes_id": False,
            }
        )
        cls.steve = cls.env["res.partner"].create(
            {
                "name": "Steve Bucknor",
                "email": "steve.bucknor@example.com",
            }
        )
        cls.order = cls.env["sale.order"].create({"partner_id": cls.steve.id})
        # Add products in order
        cls.large_cabinet_line = cls.env["sale.order.line"].create(
            {
                "product_id": cls.largeCabinet.id,
                "name": "Large Cabinet",
                "product_uom_qty": 7.0,
                "order_id": cls.order.id,
            }
        )
        cls.conference_chair_line = cls.env["sale.order.line"].create(
            {
                "product_id": cls.conferenceChair.id,
                "name": "Conference Chair",
                "product_uom_qty": 5.0,
                "order_id": cls.order.id,
            }
        )
        cls.pedal_bin_line = cls.env["sale.order.line"].create(
            {
                "product_id": cls.pedalBin.id,
                "name": "Pedal Bin",
                "product_uom_qty": 10.0,
                "order_id": cls.order.id,
            }
        )
        cls.drawer_black_line = cls.env["sale.order.line"].create(
            {
                "product_id": cls.drawerBlack.id,
                "name": "Drawer Black",
                "product_uom_qty": 2.0,
                "order_id": cls.order.id,
            }
        )

    def test_program_reward_discount_line_specific_product(self):
        """
        Test program with reward type is `discount_line` for specific product
        """
        # Now we want to apply a 10% discount for specific product Drawer Black
        coupon = self.env["coupon.program"].create(
            {
                "name": "10% reduction for specific product",
                "promo_code_usage": "no_code_needed",
                "reward_type": "discount_line",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 10.0,
                "active": True,
                "discount_apply_on": "specific_products",
                "discount_specific_product_ids": [(6, 0, [self.drawerBlack.id])],
            }
        )
        with self.assertRaises(UserError):
            coupon._onchange_discount_line_reward_type()
        goup_discount_id = self.ref("product.group_discount_per_so_line")
        self.env.user.write({"groups_id": [(4, goup_discount_id, 0)]})
        coupon._onchange_discount_line_reward_type()
        # Apply all the programs
        self.order.recompute_coupon_lines()
        # Check that Large Cabinet and Pedal Bin has discount after apply program
        self.assertEqual(
            self.large_cabinet_line.discount,
            0,
            "The discount for Large Cabinet should be empty",
        )
        self.assertEqual(
            self.drawer_black_line.discount,
            10,
            "The discount for Drawer Black should be 10%",
        )
        # Check amount total after apply coupon
        self.assertEqual(
            self.order.amount_total,
            2710.0,
            "The order total with programs should be 2710.00",
        )
        self.assertEqual(coupon.order_count, 1)
        action = coupon.action_view_sales_orders()
        self.assertEqual(action.get("domain"), [("id", "in", self.order.ids)])

    def test_program_reward_discount_line_cheapest_product(self):
        """
        Test program with reward type is `discount_line` for cheapest product
        """
        # change product line price unit
        self.large_cabinet_line.price_unit = 10
        # Now we want to apply a 10% discount for cheapest product
        coupon = self.env["coupon.program"].create(
            {
                "name": "10% reduction for cheapest product",
                "promo_code_usage": "no_code_needed",
                "reward_type": "discount_line",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 10.0,
                "active": True,
                "discount_apply_on": "cheapest_product",
            }
        )
        # Apply all the programs
        self.order.recompute_coupon_lines()
        # Check that Large Cabinet and Pedal Bin has discount after apply program
        self.assertEqual(
            self.large_cabinet_line.discount,
            10,
            "The cheapest product is Large Cabinet and discount should be 10%",
        )
        # Check amount total after apply coupon
        self.assertEqual(
            self.order.amount_total,
            2463.0,
            "The order total with programs should be 2463.00",
        )
        self.assertEqual(coupon.order_count, 1)

    def test_program_reward_discount_line_on_order(self):
        """
        Test program with reward type is `discount_line` for all lines from sale order
        """
        # Now we want to apply a 10% discount for current sale order
        coupon = self.env["coupon.program"].create(
            {
                "name": "10% reduction for current Sale Order",
                "promo_code_usage": "no_code_needed",
                "reward_type": "discount_line",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 10.0,
                "active": True,
                "discount_apply_on": "on_order",
            }
        )
        # Apply all the programs
        self.order.recompute_coupon_lines()
        # Check that paid products with discount
        self.assertEqual(
            self.large_cabinet_line.discount,
            10,
            "The discount for Large Cabinet should be 10%",
        )
        self.assertEqual(
            self.pedal_bin_line.discount, 10, "The discount for Pedal Bin should be 10%"
        )
        # Check that other products hasn't discount
        self.assertEqual(
            self.conference_chair_line.discount,
            10,
            "The discount for Conference Chair should be 10%",
        )
        self.assertEqual(
            self.drawer_black_line.discount,
            10,
            "The discount for Drawer Black should be 10%",
        )
        # Check amount total after apply coupon
        self.assertEqual(
            self.order.amount_total,
            2475.0,
            "The order total with programs should be 2475.00",
        )
        self.assertEqual(coupon.order_count, 1)

    def test_program_reward_discount_line_on_next_order_code_needed(self):
        coupon = self.env["coupon.program"].create(
            {
                "name": "10% reduction for current Sale Order",
                "promo_code_usage": "code_needed",
                "promo_applicability": "on_next_order",
                "reward_type": "discount_line",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 10.0,
                "active": True,
                "discount_apply_on": "on_order",
                "promo_code": "discount_10_percent",
            }
        )
        self.env["sale.coupon.apply.code"].with_context(active_id=self.order.id).create(
            {"coupon_code": "discount_10_percent"}
        ).process_coupon()
        self.assertEqual(
            len(coupon.coupon_ids.ids),
            1,
            "You should get a coupon for you next order that will offer a free product B",
        )
        self.order.action_confirm()
        # It should not error even if the SO does not have the requirements
        # (700$ and 1 product A), since these requirements where only used to generate
        # the coupon that we are now applying
        self.env["sale.coupon.apply.code"].with_context(active_id=self.order.id).create(
            {"coupon_code": self.order.generated_coupon_ids[0].code}
        ).process_coupon()
        self.assertEqual(len(self.order.order_line), 4)
        self.order.recompute_coupon_lines()
        self.assertEqual(len(self.order.order_line), 4)

    def test_program_reward_discount_line_on_next_order_no_code_needed(self):
        coupon = self.env["coupon.program"].create(
            {
                "name": "10% reduction for current Sale Order",
                "promo_code_usage": "no_code_needed",
                "promo_applicability": "on_next_order",
                "reward_type": "discount_line",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 10.0,
                "active": True,
                "discount_apply_on": "on_order",
            }
        )
        self.order.action_confirm()
        self.order.recompute_coupon_lines()
        self.assertEqual(
            len(coupon.coupon_ids.ids),
            1,
            "You should get a coupon for you next order that will offer 10% discount",
        )
