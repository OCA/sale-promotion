# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common


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
        cls.product_d = product_obj.create({"name": "Product A", "list_price": 80})
        cls.product_e = product_obj.create({"name": "Product E", "list_price": 70})
        cls.product_f = product_obj.create({"name": "Product F", "list_price": 60})
        loyalty_program_form = Form(
            cls.env["loyalty.program"],
            view="loyalty.loyalty_program_view_form",
        )
        loyalty_program_form.name = "Test Criteria Multi Product Program"
        loyalty_program_form.program_type = "promotion"
        loyalty_program_form.loyalty_criteria = "multi_product"
        # This is the set of criterias that the order must fulfill for the program to
        # be applied.
        #  Qty |    Products    | Repeat
        # -----|----------------|--------
        #    1 | Prod A         |
        #    2 | Prod B, Prod C |
        #    3 | Prod D, Prod E |  Yes
        with loyalty_program_form.loyalty_criteria_ids.new() as criteria:
            criteria.product_ids.add(cls.product_a)
        with loyalty_program_form.loyalty_criteria_ids.new() as criteria:
            criteria.product_ids.add(cls.product_b)
            criteria.product_ids.add(cls.product_c)
        with loyalty_program_form.loyalty_criteria_ids.new() as criteria:
            criteria.repeat_product = True
            criteria.product_ids.add(cls.product_d)
            criteria.product_ids.add(cls.product_e)
            criteria.criterian_min_quantity = 3
        cls.loyalty_program = loyalty_program_form.save()
