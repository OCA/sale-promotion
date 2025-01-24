# Copyright 2021 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class LoyaltyMultiGiftCase(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
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
        cls.partner = cls.env["res.partner"].create(
            {"name": "Mr. Odoo", "property_product_pricelist": cls.pricelist.id}
        )
        cls.product_1 = cls.env["product.product"].create(
            {"name": "Test 1", "sale_ok": True, "list_price": 50}
        )
        cls.product_2 = cls.env["product.product"].create(
            {"name": "Test 2", "sale_ok": False, "list_price": 60}
        )
        cls.product_3 = cls.env["product.product"].create(
            {"name": "Test 3", "sale_ok": False, "list_price": 70}
        )
        cls.product_4 = cls.env["product.product"].create(
            {"name": "Test 4", "sale_ok": False, "list_price": 80}
        )
        cls.loyalty_program_form = cls.env["loyalty.program"].create(
            {
                "name": "Test Multi Gift Program",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 2,
                        },
                    ),
                ],
                "reward_ids": [
                    Command.create(
                        {
                            "reward_type": "multi_gift",
                            "required_points": 1,
                            "loyalty_multi_gift_ids": [
                                Command.create(
                                    {
                                        "reward_product_ids": [
                                            Command.link(cls.product_2.id)
                                        ],
                                        "reward_product_quantity": 2,
                                    },
                                ),
                                Command.create(
                                    {
                                        "reward_product_ids": [
                                            Command.link(cls.product_3.id),
                                            Command.link(cls.product_4.id),
                                        ],
                                        "reward_product_quantity": 3,
                                    },
                                ),
                            ],
                        },
                    )
                ],
            }
        )

    def test_01_loyalty_multi_gift_ids(self):
        """Check that the records are being created without duplicates
        (Fix in write method of loyalty.program)."""
        # Initially the promotion has 2 gifts
        gift_options_qty = len(
            self.loyalty_program_form.reward_ids[0].loyalty_multi_gift_ids
        )
        self.assertEqual(gift_options_qty, 2)
        # By modifying the amount of gifts (+1) by typing in the field from reward_ids
        # (loyalty.reward), the amount of gifts increases by 1, in total 3.
        self.loyalty_program_form.reward_ids[0].write(
            {
                "loyalty_multi_gift_ids": [
                    Command.create(
                        {
                            "reward_product_ids": [Command.link(self.product_3.id)],
                            "reward_product_quantity": 1,
                        },
                    )
                ],
            }
        )
        gift_options_qty = len(
            self.loyalty_program_form.reward_ids[0].loyalty_multi_gift_ids
        )
        self.assertEqual(gift_options_qty, 3)
        # This will fail. When modifying the amount of gifts from the promotion (as it
        # is done in the form) if we increase that gift in 1 more, we should
        # have in total 4 gifts, the previous 3 + 1, in this case 2 records are being
        # created for the same gift and instead of having 4, there will be 5 (failure).
        self.loyalty_program_form.write(
            {
                "reward_ids": [
                    Command.update(
                        self.loyalty_program_form.reward_ids[0].id,
                        {
                            "loyalty_multi_gift_ids": [
                                Command.create(
                                    {
                                        "reward_product_ids": [
                                            Command.link(self.product_3.id)
                                        ],
                                        "reward_product_quantity": 1,
                                    },
                                )
                            ],
                        },
                    )
                ],
            }
        )
        gift_options_qty = len(
            self.loyalty_program_form.reward_ids[0].loyalty_multi_gift_ids
        )
        self.assertEqual(gift_options_qty, 4)

    def test_02_compute_multi_gift(self):
        """Test the computation of multi_gift field."""
        reward = self.loyalty_program_form.reward_ids[0]
        reward.reward_type = "multi_gift"
        reward.loyalty_multi_gift_ids = [Command.clear()]
        self.assertFalse(
            reward.multi_gift, "Multi gift should be False for empty gift list."
        )
        reward.loyalty_multi_gift_ids = [
            Command.create(
                {
                    "reward_product_ids": [Command.link(self.product_2.id)],
                    "reward_product_quantity": 1,
                },
            )
        ]
        self.assertTrue(
            reward.multi_gift, "Multi gift should be True for valid gift list."
        )

    def test_03_compute_description(self):
        """Test the description computation for multi_gift rewards."""
        reward = self.loyalty_program_form.reward_ids[0]
        reward.reward_type = "multi_gift"
        reward.loyalty_multi_gift_ids = [Command.clear()]  # Clear existing lines
        self.assertEqual(
            reward.description,
            "Multi Gift",
            "Description should match for empty products.",
        )
        reward.loyalty_multi_gift_ids = [
            Command.create(
                {
                    "reward_product_ids": [
                        Command.link(self.product_2.id),
                        Command.link(self.product_3.id),
                    ],
                },
            )
        ]
        self.assertIn(
            "Multi Gift -",
            reward.description,
            "Description should include product names.",
        )

    def test_04_onchange_reward_product_ids(self):
        """Test onchange logic for reward_product_ids."""
        line = self.loyalty_program_form.reward_ids[0].loyalty_multi_gift_ids[0]
        line.reward_product_ids = [Command.set([self.product_3.id, self.product_2.id])]
        line.onchange_reward_product_ids()
        self.assertEqual(
            line.reward_default_product_id.id,
            self.product_3.id,
            f"Expected {self.product_3.id} as default product, "
            f"but got {line.reward_default_product_id.id}.",
        )
