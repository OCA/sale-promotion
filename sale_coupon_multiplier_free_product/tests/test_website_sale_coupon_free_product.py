# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common


class TestSaleCouponMultiplier(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
            cls.env["sale.coupon.program"],
            view="sale_coupon.sale_coupon_program_view_promo_program_form",
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
        # We'll be using this sale order
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_1
            line_form.product_uom_qty = 2
        cls.sale = sale_form.save()

    def test_sale_coupon_test_3x2(self):
        """As we fulfill the proper product qties, we get the proper free product"""
        line = self.sale.order_line
        self.sale.recompute_coupon_lines()
        discount_line = self.sale.order_line.filtered("is_reward_line")
        self.assertEqual(self.product_1, discount_line.product_id)
        # We get the 3x2
        self.assertEqual(1, discount_line.product_uom_qty)
        self.assertEqual(0, discount_line.price_reduce)
        self.assertEqual(50, discount_line.price_unit)
        line_form = Form(line, view="sale.view_order_line_tree")
        line_form.product_uom_qty = 7
        line_form.save()
        self.sale.recompute_coupon_lines()
        discount_line = self.sale.order_line.filtered("is_reward_line")
        # We get 9x6 (there's 1 unit that can't be discounted)
        self.assertEqual(3, discount_line.product_uom_qty)
        self.assertEqual(0, discount_line.price_reduce)
        line_form.product_uom_qty = 1
        line_form.save()
        self.sale.recompute_coupon_lines()
        discount_line = self.sale.order_line.filtered("is_reward_line")
        # The discount goes away
        self.assertFalse(bool(discount_line))
        # We get a 30x20
        line_form.product_uom_qty = 20
        line_form.save()
        self.sale.recompute_coupon_lines()
        discount_line = self.sale.order_line.filtered("is_reward_line")
        self.assertEqual(10, discount_line.product_uom_qty)
        self.assertEqual(0, discount_line.price_reduce)
        # Set a max reward quantity that is less than the applicable qty
        self.coupon_program.reward_product_max_quantity = 5
        self.sale.recompute_coupon_lines()
        discount_line = self.sale.order_line.filtered("is_reward_line")
        self.assertEqual(5, discount_line.product_uom_qty)
        self.assertEqual(0, discount_line.price_reduce)
        # Now set a max reward quantity that is more than the applicable qty
        self.coupon_program.reward_product_max_quantity = 20
        self.sale.recompute_coupon_lines()
        discount_line = self.sale.order_line.filtered("is_reward_line")
        self.assertEqual(10, discount_line.product_uom_qty)
        self.assertEqual(0, discount_line.price_reduce)

    def test_buy_a_product_get_this_other_free(self):
        """For every 2 of any product, we get the rewarded product for free"""
        # Now the domain applies
        self.coupon_program.force_rewarded_product = False
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product_2
            line_form.product_uom_qty = 2
            line_form.price_unit = 50
        sale = sale_form.save()
        sale.recompute_coupon_lines()
        discount_line = sale.order_line.filtered("is_reward_line")
        # We bought 2 x product_2 and get 1x product_1
        self.assertEqual(self.product_1, discount_line.product_id)
        self.assertEqual(1, discount_line.product_uom_qty)
        self.assertEqual(0, discount_line.price_reduce)
        self.assertEqual(50, discount_line.price_unit)
        # Now we add a third product (the domain is open for every product)
        # to increase the promotion gifts
        sale_form = Form(sale)
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product_3
            line_form.product_uom_qty = 5
        sale_form.save()
        sale.recompute_coupon_lines()
        discount_line = sale.order_line.filtered("is_reward_line")
        # For every two products we get an extra gift so (5 + 2) // 2 = 3
        self.assertEqual(self.product_1, discount_line.product_id)
        self.assertEqual(3, discount_line.product_uom_qty)
        self.assertEqual(0, discount_line.price_reduce)
        self.assertEqual(50, discount_line.price_unit)
        # Set a max reward quantity that is less than the applicable qty
        self.coupon_program.reward_product_max_quantity = 1
        sale.recompute_coupon_lines()
        discount_line = sale.order_line.filtered("is_reward_line")
        self.assertEqual(1, discount_line.product_uom_qty)
        self.assertEqual(0, discount_line.price_reduce)
        # Now set a max reward quantity that is more than the applicable qty
        self.coupon_program.reward_product_max_quantity = 20
        sale.recompute_coupon_lines()
        discount_line = sale.order_line.filtered("is_reward_line")
        self.assertEqual(3, discount_line.product_uom_qty)
        self.assertEqual(0, discount_line.price_reduce)
