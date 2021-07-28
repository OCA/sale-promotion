# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import Form, common


class TestSaleCouponIncompatibility(common.SavepointCase):
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
        cls.product_a = product_obj.create({"name": "Product A"})
        cls.product_b = product_obj.create({"name": "Product B"})
        cls.product_c = product_obj.create({"name": "Product C"})

    def _create_coupon_program(
        self,
        product=False,
        criterias=False,
        code=False,
        apply_on_order=True,
        reward_type=False,
    ):
        """Helper method to create coupon programs in the tests cases"""
        coupon_program_form = Form(
            self.env["sale.coupon.program"],
            view="sale_coupon.sale_coupon_program_view_promo_program_form",
        )
        coupon_program_form.name = "Test Coupon Wizard"
        if product:
            # We don't want demo programs spoiling our tests
            coupon_program_form.rule_products_domain = "[('id', '=', %s)]" % (
                product.id
            )
        if not code:
            coupon_program_form.promo_code_usage = "no_code_needed"
        else:
            coupon_program_form.promo_code_usage = "code_needed"
            coupon_program_form.promo_code = code
        if apply_on_order:
            coupon_program_form.promo_applicability = "on_current_order"
        else:
            coupon_program_form.promo_applicability = "next_order"
        # Criterias is a list of tuples expecting
        if criterias:
            coupon_program_form.sale_coupon_criteria = "multi_product"
            for quantity, products, repeat in criterias:
                with coupon_program_form.sale_coupon_criteria_ids.new() as criteria:
                    criteria.repeat_product = repeat
                    criteria.rule_min_quantity = quantity
                    for product in products:
                        criteria.product_ids.add(product)
        coupon_program_form.reward_type = reward_type or "product"
        coupon_program_form.reward_product_id = product or self.product_a
        return coupon_program_form.save()

    def _generate_coupons(self, program, number=1):
        """Helper method to easily generate coupons in the test cases"""
        self.env["sale.coupon.generate"].with_context(active_id=program.id).create(
            {"generation_type": "nbr_coupon", "nbr_coupons": number}
        ).generate_coupon()
        return program.coupon_ids

    def _create_sale(self, partner, products=False):
        """Helper method to create sales in the test cases"""
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = partner
        if not products:
            products = self.product_a
        for product in products:
            with sale_form.order_line.new() as line_form:
                line_form.product_id = product
                line_form.product_uom_qty = 3
        return sale_form.save()

    def _apply_coupon(self, order, code):
        """Helper method to apply either coupon or progam codes. It ensures that the
        UserError exception is raised as well."""
        self.env["sale.coupon.apply.code"].with_context(active_id=order.id).create(
            {"coupon_code": code}
        ).process_coupon()

    def _open_coupon_wizard(self, order):
        """Helper method to open the selection wizard"""
        return Form(
            self.env["coupon.selection.wizard"].create({"order_id": order.id})
        ).save()

    def test_01_coupon_selection_wizard(self):
        """A program with no code and customer application limit won't be applied
        once the limit is reached"""
        # First we test the regular behavior
        promotion_1 = self._create_coupon_program(
            product=self.product_a,
            criterias=[
                (1, self.product_a, False),
                (3, self.product_b + self.product_c, True),
            ],
            reward_type="discount",
        )
        self._create_coupon_program(self.product_b)
        sale_1 = self._create_sale(self.partner_1)
        wizard = self._open_coupon_wizard(sale_1)
        self.assertEqual(wizard.available_coupon_program_ids, promotion_1)
        wizard.coupon_program_id = wizard.available_coupon_program_ids
        wizard._onchange_coupon_program_id()
        with self.assertRaises(UserError):
            wizard.apply_promotion()
        # Add some quantity for optional product 1
        wizard.promotion_line_ids[1].quantity = 2
        with self.assertRaises(UserError):
            wizard.apply_promotion()
        # Add some more quantity for optional product 1 and now the promotion can be
        # applied
        wizard.promotion_line_ids[2].quantity = 1
        wizard.apply_promotion()
        self.assertTrue(promotion_1 in sale_1.no_code_promo_program_ids)
