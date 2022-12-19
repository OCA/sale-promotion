# Copyright 2022 Dinar Gabbasov
# Copyright 2022 Ooops404
# Copyright 2022 Cetmix
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, common, tagged


@tagged("post_install", "-at_install")
class TestSaleCouponProductExclude(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        product_obj = cls.env["product.product"]
        cls.pippo = product_obj.create(
            {"name": "pippo", "list_price": 50.0, "taxes_id": False}
        )
        cls.pippo2 = product_obj.create(
            {"name": "pippo2", "list_price": 100, "taxes_id": False}
        )
        cls.largeCabinet = product_obj.create(
            {"name": "Large Cabinet", "list_price": 200.0, "taxes_id": False}
        )
        cls.conferenceChair = product_obj.create(
            {"name": "Conference Chair", "list_price": 300, "taxes_id": False}
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
        cls.steve = cls.env["res.partner"].create(
            {"name": "Steve Bucknor", "email": "steve.bucknor@example.com"}
        )
        # Let's prepare a sale order to play with
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.steve
        sale_form.pricelist_id = cls.pricelist
        with sale_form.order_line.new() as line:
            line.product_id = cls.largeCabinet
            line.product_uom_qty = 1
        with sale_form.order_line.new() as line:
            line.product_id = cls.conferenceChair
            line.product_uom_qty = 1
        with sale_form.order_line.new() as line:
            line.product_id = cls.pippo
            line.product_uom_qty = 1
        with sale_form.order_line.new() as line:
            line.product_id = cls.pippo2
            line.product_uom_qty = 1
        cls.order = sale_form.save()

    def _create_promo(self):
        """Common promo case for tests"""
        program_form = Form(
            self.env["coupon.program"],
            view="sale_coupon.sale_coupon_program_view_promo_program_form",
        )
        program_form.name = "10% Discount Excluding products with name contains pippo"
        program_form.promo_code_usage = "no_code_needed"
        program_form.reward_type = "discount"
        program_form.discount_type = "percentage"
        program_form.discount_percentage = 10.0
        program_form.exclude_products_domain = [("name", "ilike", "pippo")]
        return program_form

    def test_program_reward_discount_on_order(self):
        """
        Check that we can apply coupon to order
        except for products specified in `exclude_products_domain`
        """
        program_form = self._create_promo()
        program_form.discount_apply_on = "on_order"
        program_form.save()
        self.assertFalse(
            self.order.order_line.filtered("is_reward_line"),
            "We should not get the reduction line",
        )
        # Amount total of the
        # order = sum([line.price_unit*line.product_uom_qty for line in self.order.order_line])
        self.assertEqual(
            self.order.amount_total,
            650.0,
            "The order total with programs should be 650.00",
        )
        # Apply program
        self.order.recompute_coupon_lines()
        # Check amount total after apply coupon with ignored products: 650 - (650-150)*0.1
        self.assertEqual(
            self.order.amount_total,
            600.0,
            "The order total with programs should be 600.00",
        )

    def test_program_reward_discount_on_cheapest_product(self):
        """
        Check that the cheapest product from not excluding products
        listed in `exclude_products_domain` is found.
        """
        program_form = self._create_promo()
        program_form.discount_apply_on = "cheapest_product"
        program_form.save()
        # Amount total of the
        # order = sum([line.price_unit*line.product_uom_qty for line in self.order.order_line])
        self.assertEqual(
            self.order.amount_total,
            650.0,
            "The order total with programs should be 650.00",
        )
        # Apply program
        self.order.recompute_coupon_lines()
        # Check amount total after apply coupon with ignored products: 650 - 20
        # The discount should only be applied for found the cheapest product -
        # large Cabinet with price 200
        self.assertEqual(
            self.order.amount_total,
            630.0,
            "The order total with programs should be 630.00",
        )
