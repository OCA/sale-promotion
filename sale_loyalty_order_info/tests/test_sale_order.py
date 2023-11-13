# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.sale_loyalty.tests.common import TestSaleCouponCommon


class TestSaleOrder(TestSaleCouponCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Deactivate default promotion program
        cls.immediate_promotion_program.active = False

        cls.order = cls.env["sale.order"].create({"partner_id": cls.steve.id})

    def _create_discount_program(self, product):
        return self.env["loyalty.program"].create(
            {
                "name": "50% on order if product bought",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "company_id": self.env.company.id,
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "product_ids": [(4, product.id)],
                            "minimum_qty": 1,
                        },
                    )
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "discount",
                            "discount": 50,
                            "required_points": 1,
                        },
                    ),
                ],
            }
        )

    def _create_discount_code_program(self):
        return self.env["loyalty.program"].create(
            {
                "name": "50% on order with code 'PROMOTION'",
                "program_type": "promo_code",
                "trigger": "with_code",
                "applies_on": "current",
                "company_id": self.env.company.id,
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "code": "PROMOTION",
                        },
                    )
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "discount",
                            "discount": 50,
                            "required_points": 1,
                        },
                    ),
                ],
            }
        )

    def _create_discount_next_order(self):
        return self.env["loyalty.program"].create(
            {
                "name": "15% on next order if 50$ spent",
                "program_type": "next_order_coupons",
                "trigger": "auto",
                "applies_on": "future",
                "company_id": self.env.company.id,
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "minimum_amount": 50,
                        },
                    )
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "discount": 15,
                        },
                    )
                ],
            }
        )

    def test_empty_order(self):
        self.assertEqual(self.order.reward_amount_tax_incl, 0)
        self.assertEqual(self.order.promo_codes, "[]")
        self.assertFalse(self.order.generated_coupon_ids)
        self.assertFalse(self.order.program_ids)

    def test_reward_amount_tax_incl(self):
        program = self._create_discount_program(self.product_A)
        self.order.order_line = [
            (
                0,
                0,
                {
                    "product_id": self.product_A.id,
                },
            )
        ]
        self.order._update_programs_and_rewards()
        claimable_rewards = self.order._get_claimable_rewards()
        coupon = next(iter(claimable_rewards))
        self.order._apply_program_reward(claimable_rewards[coupon], coupon)
        self.assertAlmostEqual(
            self.order.reward_amount,
            -0.5 * self.product_A.lst_price,
            2,
            "Untaxed reward amount should be 50% of untaxed unit price of product A",
        )
        self.assertAlmostEqual(
            self.order.reward_amount_tax_incl,
            -0.5
            * self.product_A.taxes_id.compute_all(self.product_A.lst_price)[
                "total_included"
            ],
            2,
            "Tax included reward amount should be 50% of tax included unit price of product A",
        )
        self.assertEqual(self.order.program_ids.ids, [program.id])

    def test_promo_codes(self):
        program = self._create_discount_code_program()
        self.order.order_line = [
            (
                0,
                0,
                {
                    "product_id": self.product_A.id,
                },
            )
        ]
        # Apply the coupon to make it allowed in the rewards list
        self.env["sale.loyalty.coupon.wizard"].create(
            {
                "order_id": self.order.id,
                "coupon_code": "PROMOTION",
            }
        ).action_apply()
        # Apply the coupon reward
        self.env["sale.loyalty.reward.wizard"].create(
            {
                "order_id": self.order.id,
                "selected_reward_id": program.reward_ids.id,
            }
        ).action_apply()
        self.assertEqual(self.order.promo_codes, "['PROMOTION']")
        self.assertEqual(self.order.program_ids.ids, [program.id])

    def test_generated_programs(self):
        program = self._create_discount_next_order()
        self.assertGreater(self.product_A.lst_price, 50)
        self.order.order_line = [
            (
                0,
                0,
                {
                    "product_id": self.product_A.id,
                },
            )
        ]
        self.order._update_programs_and_rewards()
        self.assertTrue(self.order.generated_coupon_ids)
        self.assertEqual(self.order.generated_coupon_ids.ids, program.coupon_ids.ids)
