# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase


class TestSaleLoyaltyPartnerApplicability(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disable sharing of coupons between members of the same trading entity
        cls.env["ir.config_parameter"].set_param("allow_coupon_sharing", "False")
        product_obj = cls.env["product.product"]
        partner_obj = cls.env["res.partner"]
        cls.commercial_entity = cls.env["res.partner"].create(
            {"name": "Mr. Commercial Entity"}
        )
        cls.product_a = product_obj.create({"name": "Product A", "list_price": 50})
        cls.product_b = product_obj.create({"name": "Product B", "list_price": 10})
        cls.product_c = product_obj.create({"name": "Product C", "list_price": 70})
        cls.partner1 = partner_obj.create(
            {"name": "Mr. Partner One", "parent_id": cls.commercial_entity.id}
        )
        cls.partner2 = partner_obj.create(
            {"name": "Mr. Partner Two", "parent_id": cls.commercial_entity.id}
        )
        cls.partner3 = partner_obj.create({"name": "Mr. Partner Three"})
        cls.promotion_program = cls.env["loyalty.program"].create(
            {
                "name": "Test Promotions Sale Loyalty Partner Applicability",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "rule_partners_domain": [("id", "=", cls.partner1.id)],
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "rule_partners_domain": [("id", "=", cls.partner2.id)],
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    ),
                ],
                "reward_ids": [
                    (
                        0,
                        0,
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
        cls.promo_code_program = cls.env["loyalty.program"].create(
            {
                "name": "Test Discount Code Sale Loyalty Partner Applicability",
                "program_type": "promo_code",
                "trigger": "with_code",
                "applies_on": "current",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "code": "10DISCOUNT",
                            "rule_partners_domain": [("id", "=", cls.partner1.id)],
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "rule_partners_domain": [("id", "=", cls.partner2.id)],
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    ),
                ],
                "reward_ids": [
                    (
                        0,
                        0,
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
        cls.next_order_coupon = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Limit Next Order Coupons",
                "program_type": "next_order_coupons",
                "trigger": "auto",
                "applies_on": "future",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "rule_partners_domain": [("id", "=", cls.partner1.id)],
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    ),
                ],
                "reward_ids": [
                    (
                        0,
                        0,
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

    def _create_sale(self, partner):
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product_a
            line_form.product_uom_qty = 1
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product_b
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

    def test_01_sale_loyalty_partner_applicability_promotion(self):
        # The test is executed with a promotion which states in its rules that
        # the promotion will be applicable on partner1 and partner2.
        sale_1 = self._create_sale(self.partner1)
        self._action_apply_program(sale_1, self.promotion_program)
        self.assertTrue(bool(sale_1.order_line.filtered("is_reward_line")))
        sale_2 = self._create_sale(self.partner2)
        self._action_apply_program(sale_2, self.promotion_program)
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        sale_3 = self._create_sale(self.partner3)
        # There should be no promotion applicable, therefore the wizard should not
        # appear to choose one, therefore the error.
        with self.assertRaises(ValidationError):
            self._action_apply_program(sale_3, self.promotion_program)

    def test_02_sale_loyalty_partner_applicability_promo_code(self):
        # The test is executed with a promotion code which states in its rules that
        # the promotion will be applicable on partner1 and partner2.
        sale_1 = self._create_sale(self.partner1)
        self._apply_promo_code(sale_1, "10DISCOUNT")
        self.assertTrue(bool(sale_1.order_line.filtered("is_reward_line")))
        sale_2 = self._create_sale(self.partner2)
        self._apply_promo_code(sale_2, "10DISCOUNT")
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        sale_3 = self._create_sale(self.partner3)
        # Promotion does not apply to partner3.
        with self.assertRaises(ValidationError):
            self._apply_promo_code(sale_3, "10DISCOUNT")

    def test_03_coupon_code_next_order_customer_limit(self):
        # Enable sharing of coupons between members of the same trading entity
        self.env["ir.config_parameter"].set_param("allow_coupon_sharing", "True")
        # The first order generates the coupon for the next one
        sale_1 = self._create_sale(self.partner1)
        sale_1._update_programs_and_rewards()
        sale_1.action_confirm()
        coupon_1 = self.next_order_coupon.coupon_ids
        # New order for another member of the same trading entity to apply the
        # generated coupon
        sale_2 = self._create_sale(self.partner2)
        self._apply_promo_code(sale_2, coupon_1.code)
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        # New order to generate a coupon
        sale_3 = self._create_sale(self.partner1)
        sale_3._update_programs_and_rewards()
        sale_3.action_confirm()
        coupon_2 = self.next_order_coupon.coupon_ids[1]
        # New order for another partner from another business entity. The coupon will
        # not be applied.
        sale_4 = self._create_sale(self.partner3)
        with self.assertRaises(ValidationError):
            self._apply_promo_code(sale_4, coupon_2.code)
