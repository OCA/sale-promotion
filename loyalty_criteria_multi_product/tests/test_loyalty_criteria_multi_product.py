# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class TestLoyaltyCriteriaMultiProduct(BaseCommon):
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
        cls.partner = cls.env["res.partner"].create(
            {"name": "Mr. Odoo", "property_product_pricelist": cls.pricelist.id}
        )
        cls.product_a = product_obj.create({"name": "Product A", "list_price": 50})
        cls.product_b = product_obj.create({"name": "Product B", "list_price": 60})
        cls.product_c = product_obj.create({"name": "Product C", "list_price": 70})
        # This is the set of criterias that the order must fulfill for the program to
        # be applied.
        #  Qty |    Products    |
        # -----|----------------|
        #    1 | Prod A         |
        #    2 | Prod B, Prod C |
        cls.loyalty_program = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Criteria Multi Product",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "loyalty_criteria": "multi_product",
                            "loyalty_criteria_ids": [
                                Command.create(
                                    {
                                        "product_ids": [Command.link(cls.product_a.id)],
                                    },
                                ),
                                Command.create(
                                    {
                                        "product_ids": [
                                            Command.link(cls.product_b.id),
                                            Command.link(cls.product_c.id),
                                        ],
                                    },
                                ),
                            ],
                        },
                    ),
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "loyalty_criteria": "multi_product",
                            "loyalty_criteria_ids": [
                                Command.create(
                                    {
                                        "product_ids": [
                                            Command.link(cls.product_a.id),
                                            Command.link(cls.product_c.id),
                                        ],
                                    },
                                ),
                            ],
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

    def test_loyalty_criteria_compute_min_quantity(self):
        """Test computation of rule_min_quantity."""
        criteria = self.env["loyalty.criteria"].create(
            {
                "product_ids": [
                    Command.link(self.product_a.id),
                    Command.link(self.product_b.id),
                ]
            }
        )
        self.assertEqual(
            criteria.rule_min_quantity, 2, "Min quantity should match product count."
        )

    def test_loyalty_rule_onchange(self):
        """Test onchange behavior for loyalty criteria."""
        rule = self.env["loyalty.rule"].create(
            {
                "loyalty_criteria": "multi_product",
                "program_id": self.loyalty_program.id,
            }
        )
        rule._onchange_loyalty_criteria()
        self.assertFalse(rule.minimum_amount, "Minimum amount should be reset.")
        self.assertFalse(rule.product_ids, "Product IDs should be cleared.")
        self.assertFalse(rule.product_domain, "Product domain should be cleared.")
        self.assertFalse(
            rule.loyalty_criteria_ids, "Loyalty criteria IDs should be cleared."
        )

    def test_program_type_default_values(self):
        """Test default values for program types."""
        program_values = self.env["loyalty.program"]._program_type_default_values()
        promotion_values = program_values.get("promotion")
        self.assertIsNotNone(
            promotion_values, "Promotion type should be in the defaults."
        )
        self.assertEqual(
            promotion_values["rule_ids"][1][2].get("loyalty_criteria"),
            "domain",
            "Loyalty criteria should default to domain.",
        )
