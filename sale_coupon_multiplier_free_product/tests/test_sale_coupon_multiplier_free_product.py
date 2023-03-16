# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, tagged

from odoo.addons.coupon_multiplier_free_product.tests import TestCouponMultiplier


@tagged("post_install", "-at_install")
class TestSaleCouponMultiplier(TestCouponMultiplier):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # We'll be using this sale order
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_1
            line_form.product_uom_qty = 2
        cls.sale = sale_form.save()
        # Shortcut helper
        cls.apply_coupon = cls.env["sale.coupon.apply.code"].sudo().apply_coupon

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

    def test_coupon_progam_3x2(self):
        """Test coupons for this case"""
        self.coupon_program.program_type = "coupon_program"
        self.coupon_program.promo_code_usage = "code_needed"
        self.env["coupon.generate.wizard"].with_context(
            active_id=self.coupon_program.id
        ).create({"generation_type": "nbr_coupon", "nbr_coupons": 1}).generate_coupon()
        coupon = self.coupon_program.coupon_ids
        self.assertEqual(coupon.state, "new")
        # No discount until we apply the code
        self.sale.recompute_coupon_lines()
        discount_line = self.sale.order_line.filtered("is_reward_line")
        sale_line = self.sale.order_line
        self.assertFalse(bool(discount_line))
        self.apply_coupon(self.sale, coupon.code)
        # The discount is applied
        discount_line = self.sale.order_line.filtered("is_reward_line")
        self.assertTrue(bool(discount_line))
        # The discount remains
        self.sale.recompute_coupon_lines()
        discount_line = self.sale.order_line.filtered("is_reward_line")
        self.assertTrue(bool(discount_line))
        self.assertEqual(coupon.state, "used")
        # The coupon isn't applicable anymore
        sale_line.product_uom_qty = 1
        self.sale.recompute_coupon_lines()
        discount_line = self.sale.order_line.filtered("is_reward_line")
        self.assertFalse(bool(discount_line))
        self.assertEqual(coupon.state, "new")

    def test_coupon_buy_a_product_get_this_other_free(self):
        """For every 2 of any product, we get the rewarded product for free"""
        self.coupon_program.force_rewarded_product = False
        self.coupon_program.program_type = "coupon_program"
        self.coupon_program.promo_code_usage = "code_needed"
        self.env["coupon.generate.wizard"].with_context(
            active_id=self.coupon_program.id
        ).create({"generation_type": "nbr_coupon", "nbr_coupons": 1}).generate_coupon()
        coupon = self.coupon_program.coupon_ids
        self.assertEqual(coupon.state, "new")
        # Let's create a new sale
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product_2
            line_form.product_uom_qty = 2
            line_form.price_unit = 50
        sale = sale_form.save()
        sale_line = sale.order_line
        sale.recompute_coupon_lines()
        discount_line = sale.order_line.filtered("is_reward_line")
        # We should apply the coupon first
        self.assertFalse(bool(discount_line))
        self.apply_coupon(sale, coupon.code)
        discount_line = sale.order_line.filtered("is_reward_line")
        # We bought 2 x product_2 and get 1x product_1
        self.assertEqual(self.product_1, discount_line.product_id)
        self.assertEqual(coupon.state, "used")
        self.assertEqual(1, discount_line.product_uom_qty)
        self.assertEqual(0, discount_line.price_reduce)
        self.assertEqual(50, discount_line.price_unit)
        # The product could come with a 100% discount
        self.product_1.list_price = 0
        # We bought 5 x product_2 and get 2x product_1
        sale_line.product_uom_qty = 5
        sale.recompute_coupon_lines()
        discount_line = sale.order_line.filtered("is_reward_line")
        self.assertEqual(self.product_1, discount_line.product_id)
        self.assertEqual(2, discount_line.product_uom_qty)
        self.assertEqual(0, discount_line.price_unit)
        self.assertEqual(coupon.state, "used")
