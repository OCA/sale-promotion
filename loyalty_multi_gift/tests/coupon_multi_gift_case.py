# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, TransactionCase


class CouponMultiGiftCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
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
        coupon_program_form = Form(
            cls.env["coupon.program"],
            view="coupon.coupon_program_view_promo_program_form",
        )
        coupon_program_form.name = "Test Multiplier Program"
        coupon_program_form.promo_code_usage = "no_code_needed"
        coupon_program_form.reward_type = "multi_gift"
        # For every two products that fulfill the domain condition, we'd get 2 units
        # of product 1 and 3 units of product 3 for free
        coupon_program_form.rule_minimum_amount = 75
        # Every two we'll fulfill the condition
        coupon_program_form.rule_min_quantity = 2
        coupon_program_form.rule_products_domain = "[('id', '=', %s)]" % (
            cls.product_1.id
        )
        with coupon_program_form.coupon_multi_gift_ids.new() as reward_line:
            reward_line.reward_product_ids.add(cls.product_2)
            reward_line.reward_product_quantity = 2
        with coupon_program_form.coupon_multi_gift_ids.new() as reward_line:
            reward_line.reward_product_ids.add(cls.product_3)
            reward_line.reward_product_ids.add(cls.product_4)
            reward_line.reward_product_quantity = 3
        cls.coupon_program = coupon_program_form.save()
