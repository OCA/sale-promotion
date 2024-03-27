# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import new_test_user, tagged

from odoo.addons.sale_loyalty.tests.common import TestSaleCouponCommon


@tagged("post_install", "-at_install")
class TestSaleLoyaltyAutoRefresh(TestSaleCouponCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["loyalty.program"].search([]).write({"active": False})
        cls.promo_10 = cls.env["loyalty.program"].create(
            {
                "name": "10% Discount",
                "program_type": "promotion",
                "applies_on": "current",
                "trigger": "auto",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "minimum_amount": 500,
                        },
                    )
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "discount",
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )

        cls.partner_a = cls.env["res.partner"].create({"name": "Jean Jacques"})
        cls.user_salemanager = new_test_user(
            cls.env, login="user_salemanager", groups="sales_team.group_sale_manager"
        )
        cls.user_salemanager.company_id.auto_refresh_coupon = True
        cls.env["ir.config_parameter"].set_param(
            "sale_loyalty_auto_refresh.sale_order_triggers", "origin"
        )

    def test_01_sale_loyalty_auto_refresh_on_create(self):
        """Checks reward line proper creation after product line is added."""
        order = (
            self.env["sale.order"]
            .with_user(self.user_salemanager)
            .create(
                {
                    "partner_id": self.partner_a.id,
                    "order_line": [
                        (0, 0, {"product_id": self.product_A.id, "product_uom_qty": 5})
                    ],
                }
            )
        )
        self.assertTrue(order.coupon_point_ids)

    def test_02_sale_loyalty_auto_refresh_on_update(self):
        """Checks reward line proper update after product line is modified."""
        order = (
            self.env["sale.order"]
            .with_user(self.user_salemanager)
            .create(
                {
                    "partner_id": self.partner_a.id,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product_A.id,
                            },
                        )
                    ],
                }
            )
        )
        self.assertFalse(order.coupon_point_ids)
        if order._context.get("skip_auto_refresh_coupons"):
            order = order.with_context(skip_auto_refresh_coupons=False)
        order.order_line.write({"product_uom_qty": 5})
        self.assertTrue(order.coupon_point_ids)

    def test_03_sale_loyalty_auto_refresh_on_delete(self):
        """Checks reward line proper deletion after product line is deleted"""
        order = (
            self.env["sale.order"]
            .with_user(self.user_salemanager)
            .with_context(skip_auto_refresh_coupons=True)
            .create(
                {
                    "partner_id": self.partner_a.id,
                    "order_line": [
                        (0, 0, {"product_id": self.product_A.id, "product_uom_qty": 5}),
                        (
                            0,
                            0,
                            {
                                "product_id": self.product_B.id,
                            },
                        ),
                    ],
                }
            )
        )
        self.assertFalse(order.coupon_point_ids)
        order.order_line.filtered(
            lambda l: l.product_id == self.product_B
        ).with_context(skip_auto_refresh_coupons=False).unlink()
        self.assertTrue(order.coupon_point_ids)

    def test_04_sale_loyalty_auto_refresh_custom_triggers(self):
        """Checks reward line proper update after product line is modified"""
        order = (
            self.env["sale.order"]
            .with_user(self.user_salemanager)
            .with_context(skip_auto_refresh_coupons=True)
            .create(
                {
                    "partner_id": self.partner_a.id,
                    "order_line": [
                        (0, 0, {"product_id": self.product_A.id, "product_uom_qty": 5})
                    ],
                }
            )
        )
        self.assertFalse(order.coupon_point_ids)
        order.with_context(skip_auto_refresh_coupons=False).update(
            {"origin": "Refresh"}
        )
        self.assertTrue(order.coupon_point_ids)

    def test_05_multi_programs(self):
        promo_20 = self.promo_10.copy(
            {
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "discount",
                            "discount": 20,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ]
            }
        )
        promo_prod = self.promo_10.copy(
            {
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "product",
                            "reward_product_id": self.product_B.id,
                            "reward_product_qty": 1,
                            "required_points": 1,
                        },
                    )
                ]
            }
        )
        order = (
            self.env["sale.order"]
            .with_user(self.user_salemanager)
            .create(
                {
                    "partner_id": self.partner_a.id,
                    "order_line": [
                        (0, 0, {"product_id": self.product_A.id, "product_uom_qty": 5})
                    ],
                }
            )
        )
        self.assertTrue(order.coupon_point_ids)
        line_promo_10 = order.order_line.filtered(
            lambda line: line.reward_id == self.promo_10.reward_ids
        )
        line_promo_20 = order.order_line.filtered(
            lambda line: line.reward_id == promo_20.reward_ids
        )
        line_promo_prod = order.order_line.filtered(
            lambda line: line.reward_id == promo_prod.reward_ids
        )
        self.assertFalse(line_promo_10)  # Promo 20% is better, no select promo 10%
        self.assertTrue(line_promo_20)
        self.assertTrue(line_promo_prod)
