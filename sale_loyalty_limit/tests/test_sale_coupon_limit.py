# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import Form, common


class TestSaleCouponLimit(common.SavepointCase):
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
            cls.env["sale.coupon.program"],
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

    def _create_sale(self, partner, salesman=False):
        """Helper method to create sales in the test cases"""
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = partner
        if salesman:
            sale_form.user_id = salesman
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product_a
            line_form.product_uom_qty = 1
        return sale_form.save()

    def _apply_coupon(self, order, code, bp=False):
        """Helper method to apply either coupon or progam codes. It ensures that the
        UserError exception is raised as well."""
        self.env["sale.coupon.apply.code"].with_context(
            active_id=order.id, bp=bp
        ).create({"coupon_code": code}).process_coupon()

    def test_01_program_no_code_customer_limit(self):
        """A program with no code and customer application limit won't be applied
        once the limit is reached"""
        sale_1 = self._create_sale(self.partner_1)
        # In the case definition the program is no code, so there's nothing else to
        # setup.
        sale_1.recompute_coupon_lines()
        self.assertTrue(bool(sale_1.order_line.filtered("is_reward_line")))
        # The limit is 2, so the promotion can be placed in a second order
        sale_2 = self._create_sale(self.partner_1)
        sale_2.recompute_coupon_lines()
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        # As we reach the limit, no discount will be applied
        sale_3 = self._create_sale(self.partner_1)
        sale_3.recompute_coupon_lines()
        self.assertFalse(bool(sale_3.order_line.filtered("is_reward_line")))
        # However other partners can still enjoy the promotion
        sale_4 = self._create_sale(self.partner_2)
        sale_4.recompute_coupon_lines()
        self.assertTrue(bool(sale_4.order_line.filtered("is_reward_line")))

    def test_02_program_promo_code_customer_limit(self):
        """A program with code and customer application limit will raise an error when
        such limit is reached for a customer"""
        self.coupon_program.promo_code_usage = "code_needed"
        self.coupon_program.promo_code = "TEST-SALE-COUPON-LIMIT"
        # We apply it once for partner 1...
        sale_1 = self._create_sale(self.partner_1)
        self._apply_coupon(sale_1, "TEST-SALE-COUPON-LIMIT")
        self.assertTrue(bool(sale_1.order_line.filtered("is_reward_line")))
        # We apply it twice for partner 1...
        sale_2 = self._create_sale(self.partner_1)
        self._apply_coupon(sale_2, "TEST-SALE-COUPON-LIMIT")
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        # As we reach the limit we can't apply this code anymore
        sale_3 = self._create_sale(self.partner_1)
        with self.assertRaises(UserError):
            self._apply_coupon(sale_3, "TEST-SALE-COUPON-LIMIT")
        # We can still apply the promotion to other partners
        sale_4 = self._create_sale(self.partner_2)
        self._apply_coupon(sale_4, "TEST-SALE-COUPON-LIMIT")
        self.assertTrue(bool(sale_4.order_line.filtered("is_reward_line")))

    def test_03_coupon_code_customer_limit(self):
        """When a coupon of a customer limited program is applied, an error will raise
        when the limit is reached for a given customer."""
        # Let's generate some coupons
        self.env["sale.coupon.generate"].with_context(
            active_id=self.coupon_program.id
        ).create({"generation_type": "nbr_coupon", "nbr_coupons": 3}).generate_coupon()
        coupons = (x for x in self.coupon_program.coupon_ids)
        # We apply one coupon for partner 1...
        sale_1 = self._create_sale(self.partner_1)
        self._apply_coupon(sale_1, next(coupons).code)
        self.assertTrue(bool(sale_1.order_line.filtered("is_reward_line")))
        # We apply another coupon for partner 1...
        sale_2 = self._create_sale(self.partner_1)
        self._apply_coupon(sale_2, next(coupons).code)
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        # No coupon is applied. In Backend UI a Warning popup is raised
        last_coupon = next(coupons)
        sale_3 = self._create_sale(self.partner_1)
        with self.assertRaises(UserError):
            self._apply_coupon(sale_3, last_coupon.code)
        # We can still apply the coupon to other partners
        sale_4 = self._create_sale(self.partner_2)
        self._apply_coupon(sale_4, last_coupon.code)
        self.assertTrue(bool(sale_4.order_line.filtered("is_reward_line")))

    def test_04_coupon_code_next_order_customer_limit(self):
        """Coupons should not be generated for next orders above the customer limit"""
        self.coupon_program.promo_applicability = "on_next_order"
        # The first order generates the coupon for the next one
        sale_1 = self._create_sale(self.partner_1)
        sale_1.recompute_coupon_lines()
        sale_1.action_confirm()
        coupon_1 = sale_1.generated_coupon_ids
        self.assertTrue(bool(coupon_1), "A coupon must be generated")
        # Apply it and generate another coupon in a second sale and apply it again
        self._apply_coupon(self._create_sale(self.partner_1), coupon_1.code)
        sale_2 = self._create_sale(self.partner_1)
        sale_2.recompute_coupon_lines()
        sale_2.action_confirm()
        coupon_2 = sale_2.generated_coupon_ids
        self.assertTrue(bool(coupon_2), "A second coupon must be generated")
        self._apply_coupon(self._create_sale(self.partner_1), coupon_2.code)
        # Finally, we can't generate more coupons from this promotion for this partner
        sale_3 = self._create_sale(self.partner_1)
        sale_3.recompute_coupon_lines()
        sale_3.action_confirm()
        self.assertFalse(
            bool(sale_3.generated_coupon_ids),
            "No more coupons should be generated for this customer and program",
        )
        # Other customers can still use the program
        sale_4 = self._create_sale(self.partner_2)
        sale_4.recompute_coupon_lines()
        self.assertTrue(
            bool(sale_4.generated_coupon_ids),
            "A coupon should be generated for this customer",
        )

    def test_05_program_no_code_salesman_limit(self):
        """A program with no code and salesman application limit won't be applied
        once the limit is reached"""
        # Deactivate customer limits and avoid other salesmen using this program
        self.coupon_program.rule_max_customer_application = 0
        self.coupon_program.rule_salesmen_strict_limit = True
        # Place the first order of salesman 1
        sale_1 = self._create_sale(self.partner_1, self.salesman_1)
        sale_1.recompute_coupon_lines()
        self.assertTrue(bool(sale_1.order_line.filtered("is_reward_line")))
        # The limit is 2, so the promotion can be placed in a second order
        sale_2 = self._create_sale(self.partner_1, self.salesman_1)
        sale_2.recompute_coupon_lines()
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        # As we reach the limit, no discount will be applied
        sale_3 = self._create_sale(self.partner_1, self.salesman_1)
        sale_3.recompute_coupon_lines()
        self.assertFalse(bool(sale_3.order_line.filtered("is_reward_line")))
        # However the other salesman can still enjoy the promotion
        sale_4 = self._create_sale(self.partner_1, self.salesman_2)
        sale_4.recompute_coupon_lines()
        self.assertTrue(bool(sale_4.order_line.filtered("is_reward_line")))
        # As only the salesmen in the list can use the promotion, no other can apply it
        sale_5 = self._create_sale(self.partner_1)
        sale_5.recompute_coupon_lines()
        self.assertFalse(bool(sale_5.order_line.filtered("is_reward_line")))

    def test_06_program_promo_code_salesman_limit(self):
        """A program with code and salesman application limit will raise an error when
        such limit is reached for a salesman in the list"""
        # Deactivate customer limits and avoid other salesmen using this program
        self.coupon_program.rule_max_customer_application = 0
        self.coupon_program.rule_salesmen_strict_limit = True
        self.coupon_program.promo_code_usage = "code_needed"
        self.coupon_program.promo_code = "TEST-SALE-COUPON-LIMIT"
        # First salesman_1 order...
        sale_1 = self._create_sale(self.partner_1, self.salesman_1)
        self._apply_coupon(sale_1, "TEST-SALE-COUPON-LIMIT")
        self.assertTrue(bool(sale_1.order_line.filtered("is_reward_line")))
        # Second salesman_1 order...
        sale_2 = self._create_sale(self.partner_1, self.salesman_1)
        self._apply_coupon(sale_2, "TEST-SALE-COUPON-LIMIT")
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        # As we reach the limit we can't apply this code anymore
        sale_3 = self._create_sale(self.partner_1, self.salesman_1)
        with self.assertRaises(UserError):
            self._apply_coupon(sale_3, "TEST-SALE-COUPON-LIMIT")
        # We can still apply the promotion with the other salesman
        sale_4 = self._create_sale(self.partner_1, self.salesman_2)
        self._apply_coupon(sale_4, "TEST-SALE-COUPON-LIMIT")
        self.assertTrue(bool(sale_4.order_line.filtered("is_reward_line")))
        # But only the salesmen in the list can use the promotion, no other can apply it
        sale_5 = self._create_sale(self.partner_1)
        with self.assertRaises(UserError):
            self._apply_coupon(sale_5, "TEST-SALE-COUPON-LIMIT")

    def test_07_coupon_code_salesman_limit(self):
        """When a coupon of a salesmen limited program is applied, an error will raise
        when the limit is reached for a given salesman."""
        # Deactivate customer limits and avoid other salesmen using this program
        self.coupon_program.rule_max_customer_application = 0
        self.coupon_program.rule_salesmen_strict_limit = True
        # Let's generate some coupons
        self.env["sale.coupon.generate"].with_context(
            active_id=self.coupon_program.id
        ).create({"generation_type": "nbr_coupon", "nbr_coupons": 3}).generate_coupon()
        coupons = (x for x in self.coupon_program.coupon_ids)
        # We apply one coupon with salesman_1...
        sale_1 = self._create_sale(self.partner_1, self.salesman_1)
        self._apply_coupon(sale_1, next(coupons).code)
        self.assertTrue(bool(sale_1.order_line.filtered("is_reward_line")))
        # We apply another coupon with salesman_1...
        sale_2 = self._create_sale(self.partner_1, self.salesman_1)
        self._apply_coupon(sale_2, next(coupons).code)
        self.assertTrue(bool(sale_2.order_line.filtered("is_reward_line")))
        # An error raises as we reach the limit
        last_coupon = next(coupons)
        sale_3 = self._create_sale(self.partner_1, self.salesman_1)
        with self.assertRaises(UserError):
            self._apply_coupon(sale_3, last_coupon.code, bp=True)
        # We can't apply with salesmen not in the list either
        sale_4 = self._create_sale(self.partner_1)
        with self.assertRaises(UserError):
            self._apply_coupon(sale_4, last_coupon.code)
        # We can still apply the coupon with salesman_2
        sale_5 = self._create_sale(self.partner_1, self.salesman_2)
        self._apply_coupon(sale_5, last_coupon.code)
        self.assertTrue(bool(sale_5.order_line.filtered("is_reward_line")))
        self.coupon_program.rule_salesmen_limit_ids.mapped("rule_times_used")

    def test_08_coupon_code_next_order_salesmen_limit(self):
        """Coupons should not be generated for next orders above the salesman limit"""
        # Deactivate customer limits and avoid other salesmen using this program
        self.coupon_program.rule_max_customer_application = 0
        self.coupon_program.rule_salesmen_strict_limit = True
        self.coupon_program.promo_applicability = "on_next_order"
        # The first order generates the coupon for the next one
        sale_1 = self._create_sale(self.partner_1, self.salesman_1)
        sale_1.recompute_coupon_lines()
        sale_1.action_confirm()
        coupon_1 = sale_1.generated_coupon_ids
        self.assertTrue(bool(coupon_1), "A coupon must be generated")
        # Apply it and generate another coupon in a second sale and apply it again
        self._apply_coupon(
            self._create_sale(self.partner_1, self.salesman_1), coupon_1.code
        )
        sale_2 = self._create_sale(self.partner_1, self.salesman_1)
        sale_2.recompute_coupon_lines()
        sale_2.action_confirm()
        coupon_2 = sale_2.generated_coupon_ids
        self.assertTrue(bool(coupon_2), "A second coupon must be generated")
        self._apply_coupon(
            self._create_sale(self.partner_1, self.salesman_1), coupon_2.code
        )
        # Finally, we can't generate more coupons from this promotion for this partner
        sale_3 = self._create_sale(self.partner_1, self.salesman_1)
        sale_3.recompute_coupon_lines()
        sale_3.action_confirm()
        self.assertFalse(
            bool(sale_3.generated_coupon_ids),
            "No more coupons should be generated for this customer and program",
        )
        # Other customers can still use the program
        sale_4 = self._create_sale(self.partner_1, self.salesman_2)
        sale_4.recompute_coupon_lines()
        self.assertTrue(
            bool(sale_4.generated_coupon_ids),
            "A coupon should be generated for this customer",
        )
