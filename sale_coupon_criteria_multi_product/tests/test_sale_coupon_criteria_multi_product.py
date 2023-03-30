# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form

from odoo.addons.coupon_criteria_multi_product.tests import (
    TestCouponCriteriaMultiProduct,
)


class TestSaleCouponCriteriaMultiProduct(TestCouponCriteriaMultiProduct):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # We'll be using this sale order
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_a
            line_form.product_uom_qty = 1
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_b
            line_form.product_uom_qty = 1
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_c
            line_form.product_uom_qty = 2
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_e
            line_form.product_uom_qty = 3
        cls.sale = sale_form.save()

    def test_sale_coupon_test_criteria_multi_product(self):
        """Only when all the criterias are matched we can apply the program"""
        # The discount is correctly applied
        self.sale.recompute_coupon_lines()
        discount_line = self.sale.order_line.filtered("is_reward_line")
        self.assertTrue(bool(discount_line))
        # We can change product E by product D as the criteria is set to repeat
        line_e = self.sale.order_line.filtered(lambda x: x.product_id == self.product_e)
        line_e.product_id = self.product_d
        self.sale.recompute_coupon_lines()
        discount_line = self.sale.order_line.filtered("is_reward_line")
        self.assertTrue(bool(discount_line))
        # If the order doesn't fulfill all the criterias, the discount isn't applied
        line_e.product_uom_qty = 2
        self.sale.recompute_coupon_lines()
        discount_line = self.sale.order_line.filtered("is_reward_line")
        self.assertFalse(discount_line)
        # If the criteria doesn't repeat, all the products must be in the cart
        # Lets recover the former line qtys:
        line_e.product_uom_qty = 3
        # And now we'll remove B, that should be present
        self.sale.order_line.filtered(lambda x: x.product_id == self.product_b).unlink()
        self.sale.recompute_coupon_lines()
        discount_line = self.sale.order_line.filtered("is_reward_line")
        self.assertFalse(discount_line)
