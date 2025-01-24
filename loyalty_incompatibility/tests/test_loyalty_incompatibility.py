# Copyright 2021 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Stefan Ungureanu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class LoyaltyIncompatibilityCase(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test products
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
        cls.coupon_program_without_incompatibility = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Coupon Program Without Incompatibility",
                "trigger": "with_code",
                "program_type": "coupons",
                "applies_on": "current",
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                            "product_domain": '[["name","=","Product A"]]',
                        },
                    ),
                ],
                "reward_ids": [
                    Command.create(
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
                "incompatible_promotion_ids": [Command.link(cls.promotion.id)],
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                            "product_domain": '[["name","=","Product A"]]',
                        },
                    ),
                ],
                "reward_ids": [
                    Command.create(
                        {
                            "reward_type": "product",
                            "reward_product_id": cls.product_c.id,
                            "reward_product_qty": 5,
                        },
                    )
                ],
            }
        )
        cls.promotion_2 = cls.env["loyalty.program"].create(
            {
                "name": "Second Test Promotion",
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
                            "discount": 15,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )

    def test_incompatibility_creation(self):
        """Test that incompatibility relationships are created correctly"""
        self.assertIn(
            self.promotion,
            self.coupon_program_with_incompatibility.incompatible_promotion_ids,
            "Promotion should be in incompatible programs list",
        )
        self.assertIn(
            self.coupon_program_with_incompatibility,
            self.promotion.incompatible_promotion_ids,
            "Incompatibility should be bidirectional",
        )

    def test_multiple_incompatibilities(self):
        """Test handling multiple incompatible programs"""
        # Add another incompatible program
        self.coupon_program_with_incompatibility.write(
            {"incompatible_promotion_ids": [Command.link(self.promotion_2.id)]}
        )
        self.assertEqual(
            len(self.coupon_program_with_incompatibility.incompatible_promotion_ids),
            2,
            "Should have two incompatible programs",
        )
        self.assertIn(
            self.coupon_program_with_incompatibility,
            self.promotion_2.incompatible_promotion_ids,
            "New incompatibility should be bidirectional",
        )
