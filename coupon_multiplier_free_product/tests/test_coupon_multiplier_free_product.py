# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common, tagged


@tagged("post_install", "-at_install")
class TestCouponMultiplier(common.TransactionCase):
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
            {"name": "Test 1", "list_price": 50}
        )
        cls.product_2 = cls.env["product.product"].create(
            {"name": "Test 2", "sale_ok": True}
        )
        cls.product_3 = cls.env["product.product"].create(
            {"name": "Test 3", "sale_ok": True}
        )
        coupon_program_form = Form(
            cls.env["coupon.program"],
            view="coupon.coupon_program_view_promo_program_form",
        )
        coupon_program_form.name = "Test Multiplier Program"
        coupon_program_form.promo_code_usage = "no_code_needed"
        coupon_program_form.reward_type = "multiple_of"
        coupon_program_form.reward_product_id = cls.product_1
        coupon_program_form.discount_apply_on = "on_order"
        coupon_program_form.rule_minimum_amount = 75
        # This would be a 3x2 offer. So for every 2 units of the domain products
        # we'd get the reward product
        coupon_program_form.rule_min_quantity = 2  # Every two...
        coupon_program_form.reward_product_quantity = 1  # ...you get one for free!
        # Ignore the domain and always apply over the rewarded product
        coupon_program_form.force_rewarded_product = True
        cls.coupon_program = coupon_program_form.save()
