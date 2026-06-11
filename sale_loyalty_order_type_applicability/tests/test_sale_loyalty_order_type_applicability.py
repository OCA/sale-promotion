# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestSaleLoyaltyOrderTypeApplicability(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Product", "list_price": 100}
        )
        cls.product_gift = cls.env["product.product"].create(
            {"name": "Product Gift", "list_price": 0.1}
        )
        cls.order_type_allowed = cls.env["sale.order.type"].create(
            {"name": "Order Type Loyalty Allowed"}
        )
        cls.order_type_restricted = cls.env["sale.order.type"].create(
            {"name": "Order Type Loyalty Restricted"}
        )
        cls.program_promotion = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Program",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    )
                ],
                "reward_ids": [
                    Command.create(
                        {
                            "reward_type": "discount",
                            "required_points": 1,
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )
        cls.program_next_order_coupons = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Limit Next Order Coupons",
                "program_type": "next_order_coupons",
                "trigger": "auto",
                "applies_on": "future",
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                            "reward_point_amount": 10,
                        },
                    ),
                ],
                "reward_ids": [
                    Command.create(
                        {
                            "reward_type": "discount",
                            "required_points": 1,
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )

    def _restrict_program(self, program):
        """Help method to restrict loyalty programs"""
        program.write(
            {"sale_order_type_ids": [Command.link(self.order_type_allowed.id)]}
        )

    def _create_sale(self, order_type):
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        sale_form.type_id = order_type
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1
        return sale_form.save()

    def _action_apply_program(self, sale, program):
        sale._update_programs_and_rewards()
        wizard = (
            self.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=sale)
            .create({"selected_reward_id": program.reward_ids.id})
        )
        wizard.action_apply()

    def _apply_promo_code(self, order, code):
        status = order._try_apply_code(code)
        # Check for error when applying the code and throw exception
        if "error" in status:
            raise ValidationError(status["error"])
        coupons = self.env["loyalty.card"]
        rewards = self.env["loyalty.reward"]
        for coupon, coupon_rewards in status.items():
            coupons |= coupon
            rewards |= coupon_rewards
        if len(coupons) == 1 and len(rewards) == 1:
            status = order._apply_program_reward(rewards, coupons)

    def test_01_sale_loyalty_order_type_applicability_program_promotion(self):
        # Apply promotions without sale type restrictions.
        sale_1 = self._create_sale(self.order_type_allowed)
        self._action_apply_program(sale_1, self.program_promotion)
        self.assertTrue(bool(sale_1.order_line.filtered("is_reward_line")))
        # Apply promotions with the allowed order type
        self._restrict_program(self.program_promotion)
        sale_2 = self._create_sale(self.order_type_allowed)
        self._action_apply_program(sale_2, self.program_promotion)
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        # Apply promotions with the restricted type.
        # There should be no promotion applicable, therefore the wizard should not
        # appear to choose one, therefore the error.
        sale_3 = self._create_sale(self.order_type_restricted)
        with self.assertRaises(ValidationError):
            self._action_apply_program(sale_3, self.program_promotion)

    def test_02_sale_loyalty_order_type_applicability_next_order_coupons(self):
        # The first order generates the coupon for the next ones
        sale_1 = self._create_sale(self.order_type_allowed)
        sale_1._update_programs_and_rewards()
        sale_1.action_confirm()
        coupon = self.program_next_order_coupons.coupon_ids.filtered(
            lambda x: x.order_id == sale_1
        )
        # Apply the coupon to a new order without restrictions
        sale_2 = self._create_sale(self.order_type_allowed)
        self._apply_promo_code(sale_2, coupon.code)
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        # Apply the coupon to a new order with the allowed type
        self._restrict_program(self.program_next_order_coupons)
        sale_3 = self._create_sale(self.order_type_allowed)
        self._apply_promo_code(sale_3, coupon.code)
        self.assertTrue(bool(sale_3.order_line.filtered("is_reward_line")))
        # Try to apply coupon to a new order with the restricted type.abs
        # The coupon will not be applied.
        sale_4 = self._create_sale(self.order_type_restricted)
        with self.assertRaises(ValidationError):
            self._apply_promo_code(sale_4, coupon.code)
