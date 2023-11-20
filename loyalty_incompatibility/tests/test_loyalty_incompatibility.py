# Copyright 2021 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Stefan Ungureanu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase


class LoyaltyIncompatibilityCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_obj = cls.env["product.product"]
        cls.partner = cls.env["res.partner"].create({"name": "Sailor Moon"})
        cls.product_a = product_obj.create({"name": "Product A", "list_price": 50})
        cls.product_b = product_obj.create({"name": "Product B", "list_price": 10})
        cls.product_c = product_obj.create({"name": "Product C", "list_price": 70})
        cls.promotion = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Promotion",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
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
        cls.coupon_program_without_incompatibility = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Coupon Program Without Incompatibility",
                "trigger": "with_code",
                "program_type": "coupons",
                "applies_on": "current",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                            "product_domain": '[["name","=","Product A"]]',
                        },
                    ),
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "product",
                            "reward_product_id": cls.product_c.id,
                            "reward_product_qty": 5,
                        },
                    )
                ],
            }
        )
        cls.coupon_program_with_incompatibility = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Coupon Program With Incompatibility",
                "trigger": "with_code",
                "program_type": "coupons",
                "applies_on": "current",
                "incompatible_promotion_ids": [(4, cls.promotion.id)],
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                            "product_domain": '[["name","=","Product A"]]',
                        },
                    ),
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "product",
                            "reward_product_id": cls.product_c.id,
                            "reward_product_qty": 5,
                        },
                    )
                ],
            }
        )
