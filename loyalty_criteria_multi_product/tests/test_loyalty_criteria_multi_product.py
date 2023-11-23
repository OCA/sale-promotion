# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import common


class TestLoyaltyCriteriaMultiProduct(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_obj = cls.env["product.product"]
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test pricelist",
                "item_ids": [
                    (
                        0,
                        0,
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
                    (
                        0,
                        0,
                        {
                            "reward_point_mode": "order",
                            "loyalty_criteria": "multi_product",
                            "loyalty_criteria_ids": [
                                (
                                    0,
                                    0,
                                    {
                                        "product_ids": [(4, cls.product_a.id)],
                                    },
                                ),
                                (
                                    0,
                                    0,
                                    {
                                        "product_ids": [
                                            (4, cls.product_b.id),
                                            (4, cls.product_c.id),
                                        ],
                                    },
                                ),
                            ],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "reward_point_mode": "order",
                            "loyalty_criteria": "multi_product",
                            "loyalty_criteria_ids": [
                                (
                                    0,
                                    0,
                                    {
                                        "product_ids": [
                                            (4, cls.product_a.id),
                                            (4, cls.product_c.id),
                                        ],
                                    },
                                ),
                            ],
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
