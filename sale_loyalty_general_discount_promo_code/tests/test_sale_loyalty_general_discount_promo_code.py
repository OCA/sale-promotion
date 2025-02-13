from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import format_amount


class TestSaleOrderRewards(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].set_param(
            "sale_loyalty_general_discount_promo_code."
            "automatically_apply_promo_code_discount_percentage",
            True,
        )
        self.currency = self.env.ref("base.USD")
        self.pricelist = self.env["product.pricelist"].create(
            {"name": "Test Pricelist", "currency_id": self.currency.id}
        )
        self.product_1 = self.env["product.product"].create(
            {"name": "Product 1", "lst_price": 100}
        )
        self.product_2 = self.env["product.product"].create(
            {"name": "Product 2", "lst_price": 50}
        )
        self.partner = self.env["res.partner"].create({"name": "Test Customer"})
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
            }
        )
        self.line_1 = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product_1.id,
                "price_unit": 100,
                "product_uom_qty": 1,
            }
        )
        self.line_2 = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product_2.id,
                "price_unit": 50,
                "product_uom_qty": 1,
            }
        )
        self.program = self.env["loyalty.program"].create(
            {
                "name": "Test Program",
                "program_type": "coupons",
            }
        )
        self.loyalty_rule = self.env["loyalty.rule"].create(
            {
                "program_id": self.program.id,
                "minimum_qty": 1,
            }
        )
        self.reward = self.env["loyalty.reward"].create(
            {
                "reward_type": "discount",
                "discount_mode": "percent",
                "discount": 10,
                "discount_applicability": "order",
                "program_id": self.program.id,
            }
        )
        self.coupon = self.env["loyalty.card"].create(
            {
                "code": "coupon_code_test",
                "program_id": self.program.id,
                "partner_id": self.partner.id,
                "points": 1,
            }
        )

    def test_get_total_saving_order(self):
        """Test discount applied on entire order"""
        saving = self.sale_order._get_total_saving_order(self.reward)
        self.assertEqual(saving, 15, "Total saving for order should be 15 (10% of 150)")

    def test_get_total_saving_specific(self):
        """Test discount applied on specific products"""
        self.reward.discount_applicability = "specific"
        self.reward.discount_product_ids = [(6, 0, [self.product_1.id])]
        saving = self.sale_order._get_total_saving_specific(self.reward)
        self.assertEqual(
            saving, 10, "Total saving for specific product should be 10 (10% of 100)"
        )

    def test_get_total_saving_cheapest(self):
        """Test discount applied on cheapest product"""
        self.reward.discount_applicability = "cheapest"
        saving = self.sale_order._get_total_saving_cheapest(self.reward)
        self.assertEqual(
            saving, 5, "Total saving for cheapest product should be 5 (10% of 50)"
        )

    def test_get_reward_values_discount_with_coupon_program(self):
        """Test reward values formatting and discount application"""
        rewards = self.sale_order._get_reward_values_discount(self.reward, self.coupon)
        formatted_amount = format_amount(self.env, 15, self.currency)
        self.assertIn(
            f"You saved {formatted_amount} with promo '{self.reward.program_id.name}'",
            rewards[0]["name"],
        )
        self.assertEqual(
            rewards[0]["price_unit"], 0, "Discounted reward should have price_unit = 0"
        )

    def test_apply_coupon_code(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "date_order": fields.Datetime.now(),
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref("product.product_product_8").id,
                            "name": "Product 1",
                            "product_uom_qty": 1,
                            "price_unit": 100,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref("product.product_product_5").id,
                            "name": "Product 2",
                            "product_uom_qty": 1,
                            "price_unit": 50,
                        },
                    ),
                ],
            }
        )
        coupon = self.env["loyalty.card"].create(
            {
                "code": "coupon_code_test_2",
                "program_id": self.program.id,
                "partner_id": self.partner.id,
                "points": 1,
            }
        )
        self.assertEqual(order.order_line.mapped("price_unit"), [100, 50])
        self.assertEqual(order.order_line.mapped("price_subtotal"), [100, 50])
        self.assertEqual(len(order.order_line), 2)

        # Apply coupon code
        status = order._try_apply_code(coupon.code)
        if "error" in status:
            raise ValidationError(status["error"])
        coupons = self.env["loyalty.card"]
        rewards = self.env["loyalty.reward"]
        for coupon, coupon_rewards in status.items():
            coupons |= coupon
            rewards |= coupon_rewards
        if len(coupons) == 1 and len(rewards) == 1:
            status = order._apply_program_reward(rewards, coupons)

        self.assertEqual(order.order_line.mapped("price_subtotal"), [90, 45, 0])
        self.assertEqual(len(order.order_line), 3)
        self.assertIn("line_note", order.order_line.mapped("display_type"))
