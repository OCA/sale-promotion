# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class LoyaltyLimitCase(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_obj = cls.env["product.product"]
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test pricelist",
                "item_ids": [
                    Command.create(
                        {
                            "applied_on": "3_global",
                            "compute_price": "formula",
                            "base": "list_price",
                        },
                    )
                ],
            }
        )
        cls.partner_1 = cls.env["res.partner"].create(
            {"name": "Mr. Odoo", "property_product_pricelist": cls.pricelist.id}
        )
        cls.partner_2 = cls.env["res.partner"].create(
            {"name": "Mrs. Odoo", "property_product_pricelist": cls.pricelist.id}
        )
        cls.salesman_1 = cls.env["res.users"].create(
            {"name": "Salesman 1", "login": "test_salesman_1"}
        )
        cls.salesman_2 = cls.env["res.users"].create(
            {"name": "Salesman 2", "login": "test_salesman_2"}
        )
        cls.product_a = product_obj.create({"name": "Product A", "list_price": 50})
        cls.promotion_with_customer_limit = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Limit Promotion With Customer Limit",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "max_customer_application": 2,
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
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
        cls.promotion_with_salesman_limit = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Limit Promotion With Salesman Limit",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "salesmen_limit_ids": [
                    Command.create(
                        {
                            "user_id": cls.salesman_1.id,
                            "max_salesman_application": 2,
                        },
                    ),
                    Command.create(
                        {
                            "user_id": cls.salesman_2.id,
                            "max_salesman_application": 2,
                        },
                    ),
                ],
                "salesmen_strict_limit": False,
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
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
        cls.coupon_program_with_customer_limit = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Limit Coupon With Customer Limit",
                "trigger": "with_code",
                "program_type": "coupons",
                "applies_on": "current",
                "max_customer_application": 2,
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
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
        cls.coupon_program_with_salesman_limit = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Limit Coupon With Salesman Limit",
                "trigger": "with_code",
                "program_type": "coupons",
                "applies_on": "current",
                "salesmen_limit_ids": [
                    Command.create(
                        {
                            "user_id": cls.salesman_1.id,
                            "max_salesman_application": 2,
                        },
                    ),
                    Command.create(
                        {
                            "user_id": cls.salesman_2.id,
                            "max_salesman_application": 2,
                        },
                    ),
                ],
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
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
        cls.next_order_coupon_with_customer_limit = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Limit Next Order Coupons With Customer Limit",
                "program_type": "next_order_coupons",
                "trigger": "auto",
                "applies_on": "future",
                "max_customer_application": 2,
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                            "minimum_amount": 20,
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
        cls.next_order_coupon_with_salesman_limit = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Limit Next Order Coupons With Salesman Limit",
                "program_type": "next_order_coupons",
                "trigger": "auto",
                "applies_on": "future",
                "salesmen_limit_ids": [
                    Command.create(
                        {
                            "user_id": cls.salesman_1.id,
                            "max_salesman_application": 2,
                        },
                    ),
                    Command.create(
                        {
                            "user_id": cls.salesman_2.id,
                            "max_salesman_application": 2,
                        },
                    ),
                ],
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                            "minimum_amount": 20,
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

    def test_salesmen_limit_fields_default_computation(self):
        """Test that the default computation sets limit counts to 0."""
        program = self.promotion_with_salesman_limit
        self.assertEqual(
            program.salesmen_limit_count,
            0,
            "Expected salesmen_limit_count to be 0 by default",
        )
        self.assertEqual(
            program.salesmen_limit_used_count,
            0,
            "Expected salesmen_limit_used_count to be 0 by default",
        )
        for limit in program.salesmen_limit_ids:
            self.assertEqual(
                limit.times_used, 0, "Expected times_used to be 0 by default"
            )
