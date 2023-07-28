from odoo.tests import Form, common, tagged


@tagged("post_install", "-at_install")
class TestSaleCouponDomainProductRewardFixedPrice(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        product_obj = cls.env["product.product"]
        cls.largePhone = product_obj.create(
            {"name": "Large Phone", "list_price": 100.0, "taxes_id": False}
        )
        cls.smallPhone = product_obj.create(
            {"name": "Small Phone", "list_price": 50, "taxes_id": False}
        )
        cls.simpleProduct = product_obj.create(
            {"name": "Simple Product", "list_price": 150, "taxes_id": False}
        )

        cls.steve = cls.env["res.partner"].create(
            {"name": "Steve Bucknor", "email": "steve.bucknor@example.com"}
        )
        # Ensure tests on different CI localizations
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test pricelist1",
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
        # Let's prepare a sale order to play with
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.steve
        sale_form.pricelist_id = cls.pricelist
        with sale_form.order_line.new() as line:
            line.product_id = cls.largePhone
            line.product_uom_qty = 1
        with sale_form.order_line.new() as line:
            line.product_id = cls.smallPhone
            line.product_uom_qty = 1
        with sale_form.order_line.new() as line:
            line.product_id = cls.simpleProduct
            line.product_uom_qty = 1

        cls.order = sale_form.save()
        cls.env.user.write(
            {"groups_id": [(4, cls.env.ref("product.group_discount_per_so_line").id)]}
        )

    def test_program_reward_fixed_price_with_domain_matching(self):
        """
        Test program with reward type is `fixed_price` for domain matching of product
        """
        program_form = Form(
            self.env["coupon.program"],
            view="sale_coupon.sale_coupon_program_view_promo_program_form",
        )
        program_form.name = '10% reduction if the name of the product contains "Phone"'
        program_form.promo_code_usage = "no_code_needed"
        program_form.reward_type = "fixed_price"
        program_form.discount_type = "percentage"
        program_form.discount_percentage = 10.0
        program_form.rule_products_domain = "[('name', 'ilike', 'Phone')]"
        program_form.discount_apply_on = "specific_products"
        program_form.price_unit = 20.0

        program_form.discount_apply_on_domain_product = True
        program_form.save()
        self.assertFalse(
            self.order.order_line.filtered("is_reward_line"),
            "We should not get the reduction line",
        )
        # Amount total of the
        # order = sum([line.price_unit*line.product_uom_qty for line in self.order.order_line])
        self.assertEqual(
            self.order.amount_total,
            300.0,
            "The order total with programs should be 300.00",
        )
        # Apply all the programs
        self.order.recompute_coupon_lines()
        line = self.order.order_line.filtered("is_reward_line")
        self.assertFalse(bool(line), "We should not get the reduction line")
        # Check amount total after apply coupon: 20+20+150
        self.assertEqual(
            self.order.amount_total,
            190.0,
            "The order total with programs should be 190.0",
        )
        self.assertEqual(
            self.order.order_line.filtered(
                lambda line: line.product_id == self.largePhone
            ).price_unit,
            20,
            "The discount for Large Phone should be 20",
        )
        self.assertEqual(
            self.order.order_line.filtered(
                lambda line: line.product_id == self.smallPhone
            ).price_unit,
            20,
            "The discount for Small Phone should be 20",
        )
