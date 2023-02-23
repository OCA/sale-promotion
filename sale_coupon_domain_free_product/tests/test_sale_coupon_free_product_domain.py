# Copyright 2022 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Stefan Ungureanu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form

from odoo.addons.coupon_domain_free_product.tests.test_coupon_free_product_domain import (
    TestCouponFreeProductDomain,
)


class TestSaleCouponFreeProductDomain(TestCouponFreeProductDomain):
    # We'll be using this sale order
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_1
            line_form.product_uom_qty = 2
        cls.sale = sale_form.save()

    def refresh_coupons(self, sale):
        """Auxiliar method to trigger promos recompute an return resulting lines"""
        sale.recompute_coupon_lines()
        reward_lines = self.sale._get_reward_lines()
        return (self.sale.order_line - reward_lines), reward_lines

    def get_line(self, lines, product):
        """Auxiliar method to rapidly get the product line"""
        return lines.filtered(lambda x: x.product_id == product)

    def add_product(self, sale, product, qty=1):
        """Auxiliar method to quickly add products to a sale order"""
        sale_form = Form(sale)
        with sale_form.order_line.new() as line_form:
            line_form.product_id = product
            line_form.product_uom_qty = qty
        sale_form.save()

    def test_01_sale_coupon_test_product_domain(self):
        """As we fulfill the proper product qties, we get the proper free product"""
        lines, reward_lines = self.refresh_coupons(self.sale)
        self.assertEqual(len(reward_lines), 1, "There should be only one reward")
        self.assertEqual(reward_lines.product_uom_qty, 1, "We should reward 1 unit")
        self.assertEqual(
            reward_lines.product_id,
            self.product_1,
            "The reward product should be Product 1",
        )
        self.get_line(lines, self.product_1).product_uom_qty = 4
        lines, reward_lines = self.refresh_coupons(self.sale)
        self.assertEqual(reward_lines.product_uom_qty, 2, "We should reward 2 units")
        self.add_product(self.sale, self.product_2, qty=1)
        lines, reward_lines = self.refresh_coupons(self.sale)
        self.assertEqual(len(reward_lines), 2, "We should have two rewards")
        self.coupon_program.strict_per_product_limit = True
        lines, reward_lines = self.refresh_coupons(self.sale)
        self.assertEqual(
            len(reward_lines), 1, "With strict limits only Product 1 should be rewarded"
        )
        self.get_line(lines, self.product_2).product_uom_qty = 2
        lines, reward_lines = self.refresh_coupons(self.sale)
        self.assertEqual(
            len(reward_lines),
            2,
            "As Product 2 now fulfills the conditions, it should be rewarded",
        )
        self.add_product(self.sale, self.product_3, qty=6)
        self.add_product(self.sale, self.product_4, qty=5)
        lines, reward_lines = self.refresh_coupons(self.sale)
        self.assertEqual(
            len(reward_lines), 2, "Just product 1 and product 2 should be rewarded"
        )
        self.coupon_program.rule_products_domain = "[('id', 'in', (%s, %s, %s))]" % (
            self.product_1.id,
            self.product_2.id,
            self.product_3.id,
        )
        lines, reward_lines = self.refresh_coupons(self.sale)
        self.assertEqual(
            len(reward_lines),
            3,
            "We added product 3 to the rules, so it should be in the rewards",
        )
        p1_r_line = self.get_line(reward_lines, self.product_1)
        p2_r_line = self.get_line(reward_lines, self.product_2)
        p3_r_line = self.get_line(reward_lines, self.product_3)
        self.assertEqual(p1_r_line.product_uom_qty, 2, "Product 1: We shoul 3x2 twice")
        self.assertEqual(
            p2_r_line.product_uom_qty, 1, "Product 2: We shoul 3x2 just once"
        )
        self.assertEqual(
            p3_r_line.product_uom_qty, 3, "Product 3: We shoul 3x2 three times"
        )

    def test_02_sale_coupon_free_product_domain_count(self):
        """We have to count the orders in a different manner than the core method"""
        self.assertEqual(self.coupon_program.order_count, 0)
        self.sale.recompute_coupon_lines()
        self.sale.action_confirm()
        self.coupon_program._compute_order_count()
        self.assertEqual(self.coupon_program.order_count, 1)
        # Let's place a second order
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product_1
            line_form.product_uom_qty = 2
        sale_2 = sale_form.save()
        sale_2.recompute_coupon_lines()
        sale_2.action_confirm()
        self.coupon_program._compute_order_count()
        self.assertEqual(self.coupon_program.order_count, 2)
        # We should get our order when we click in the orders smart button
        action_domain = self.coupon_program.action_view_sales_orders()["domain"]
        self.assertEqual(
            self.env["sale.order"].search(action_domain), self.sale + sale_2
        )
