# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, TransactionCase


class CouponLimitCase(TransactionCase):
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
        coupon_program_form = Form(
            cls.env["coupon.program"],
            view="sale_coupon.sale_coupon_program_view_promo_program_form",
        )
        coupon_program_form.name = "Test Coupon Limit"
        # We don't want demo programs spoiling our tests
        coupon_program_form.rule_products_domain = "[('id', '=', %s)]" % (
            cls.product_a.id
        )
        coupon_program_form.promo_code_usage = "no_code_needed"
        coupon_program_form.reward_type = "discount"
        coupon_program_form.discount_apply_on = "on_order"
        coupon_program_form.discount_type = "percentage"
        coupon_program_form.discount_percentage = 10
        # Customer limits preceed salesmen limits
        coupon_program_form.rule_max_customer_application = 2
        with coupon_program_form.rule_salesmen_limit_ids.new() as salesman_limit:
            salesman_limit.rule_user_id = cls.salesman_1
            salesman_limit.rule_max_salesman_application = 2
        with coupon_program_form.rule_salesmen_limit_ids.new() as salesman_limit:
            salesman_limit.rule_user_id = cls.salesman_2
            salesman_limit.rule_max_salesman_application = 2
        # With any other salesman, the limits won't apply
        coupon_program_form.rule_salesmen_strict_limit = False
        cls.coupon_program = coupon_program_form.save()
