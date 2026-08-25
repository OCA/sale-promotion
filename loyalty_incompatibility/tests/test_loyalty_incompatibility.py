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

    def test_incompatibility_not_propagated_between_programs(self):
        """Sharing a counterpart must not make two programs incompatible.

        With A ⊥ {B, C}, setting D ⊥ {B} must leave D incompatible with B
        only: C is unrelated to D and must stay out of it.
        """
        program_b = self.promotion
        program_c = self.promotion_2
        program_a = self.coupon_program_with_incompatibility
        program_d = self.coupon_program_without_incompatibility

        program_a.incompatible_promotion_ids = [
            Command.set((program_b | program_c).ids)
        ]
        program_d.incompatible_promotion_ids = [Command.set(program_b.ids)]

        self.assertEqual(
            program_d.incompatible_promotion_ids,
            program_b,
            "Only the selected program must be incompatible with D.",
        )
        self.assertNotIn(
            program_d,
            program_c.incompatible_promotion_ids,
            "C was never selected on D and must not gain it back.",
        )

    def test_incompatibility_removal_is_symmetric(self):
        """Removing a counterpart clears the relation on both sides."""
        program_a = self.coupon_program_with_incompatibility
        program_b = self.promotion

        self.assertIn(program_b, program_a.incompatible_promotion_ids)

        program_a.incompatible_promotion_ids = [Command.clear()]

        self.assertFalse(program_a.incompatible_promotion_ids)
        self.assertNotIn(program_a, program_b.incompatible_promotion_ids)
