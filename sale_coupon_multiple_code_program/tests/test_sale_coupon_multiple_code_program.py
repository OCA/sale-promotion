# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common, tagged


@tagged("post_install", "-at_install")
class TestSaleCouponMultiCodeProgram(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        product_obj = cls.env["product.product"]
        cls.tax = cls.env["account.tax"].create(
            {
                "name": "Test Tax 10%",
                "amount_type": "percent",
                "amount": 10.0,
                "type_tax_use": "sale",
            }
        )
        cls.product1 = product_obj.create(
            {
                "name": "Test prod 1",
                "list_price": 50.0,
                "taxes_id": [(6, 0, [cls.tax.id])],
            }
        )
        cls.product2 = product_obj.create(
            {
                "name": "Test prod 2",
                "list_price": 60.0,
                "taxes_id": [(6, 0, [cls.tax.id])],
            }
        )
        # Ensure tests on different CI localizations
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
        # Let's prepare a sale order to play with
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line:
            line.product_id = cls.product1
            line.product_uom_qty = 7
        with sale_form.order_line.new() as line:
            line.product_id = cls.product2
            line.product_uom_qty = 5
        # Order total amount will be 650
        cls.order = sale_form.save()
        # Shortcut helper
        cls.apply_coupon = cls.env["sale.coupon.apply.code"].sudo().apply_coupon

    def _create_promo(self, code=False, **options):
        """Common promo helper for tests"""
        reward_type = options.get("reward_type", "discount")
        program_form = Form(
            self.env["coupon.program"],
            view="sale_coupon.sale_coupon_program_view_promo_program_form",
        )
        program_form.name = f"Test {reward_type} promo {f'[{code}]' if code else ''}"
        program_form.rule_products_domain = options.get("domain")
        program_form.promo_code_usage = options.get(
            "promo_code_usage", "no_code_needed"
        )
        program_form.reward_type = reward_type
        program_form.promo_code = code
        program_form.rule_min_quantity = options.get("min_qty", 1)
        if reward_type == "product":
            program_form.reward_product_id = options.get(
                "reward_product_id", self.product2
            )
        elif reward_type == "discount":
            program_form.discount_percentage = options.get("discount", 50.0)
        return program_form

    def _assertPromo(self, order, reward, amount_total):
        """Common asserts"""
        reward_lines = self.order.order_line.filtered("is_reward_line")
        reward_str = f"We should {'' if reward else 'not'} get the reduction line"
        if reward:
            self.assertTrue(reward_lines, reward_str)
        else:
            self.assertFalse(reward_lines, reward_str)
        self.assertAlmostEqual(
            self.order.amount_total,
            amount_total,
            2,
            f"The order total should be {amount_total:.2f}",
        )

    def test_01_multiple_code_programs(self):
        """Apply as many coupon code programs as we want to"""
        # Discount 50% with code
        self._create_promo(code="TEST-DISC-vo8riQ9j").save()
        # Reward a unit of product 2
        self._create_promo(
            code="TEST-PROD-Y5aakjhW",
            reward_type="product",
            min_qty=4,
            domain=[("id", "=", self.product2.id)],
        ).save()
        # The promos are `no_code_needed` but as they have a promo code set they
        # can't be autoloaded.
        self.order.recompute_coupon_lines()
        # We don't have promos applied
        self._assertPromo(self.order, reward=False, amount_total=715.0)
        # Let's apply the first promo
        self.apply_coupon(self.order, "TEST-PROD-Y5aakjhW")
        self._assertPromo(self.order, reward=True, amount_total=649.0)
        # Now for the second which is a code one as well
        self.apply_coupon(self.order, "TEST-DISC-vo8riQ9j")
        self._assertPromo(self.order, reward=True, amount_total=324.5)
        # Promotions should remain even if we refresh manually
        self.order.recompute_coupon_lines()
        self._assertPromo(self.order, reward=True, amount_total=324.5)
