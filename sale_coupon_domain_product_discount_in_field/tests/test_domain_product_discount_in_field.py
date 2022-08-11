# Copyright 2022 Ooops404
# Copyright 2022 Dinar Gabbasov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common, tagged


@tagged("post_install", "-at_install")
class TestSaleCouponDomainProductDiscountInField(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        product_obj = cls.env["product.product"]
        cls.largeCabinet = product_obj.create(
            {"name": "Large Cabinet", "list_price": 100.0, "taxes_id": False}
        )
        cls.smallCabinet = product_obj.create(
            {"name": "Small Cabinet", "list_price": 50, "taxes_id": False}
        )
        cls.roundtable = product_obj.create(
            {"name": "Roundtable", "list_price": 150, "taxes_id": False}
        )
        cls.steve = cls.env["res.partner"].create(
            {"name": "Steve Bucknor", "email": "steve.bucknor@example.com"}
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
        # Let's prepare a sale order to play with
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.steve
        sale_form.pricelist_id = cls.pricelist
        with sale_form.order_line.new() as line:
            line.product_id = cls.largeCabinet
            line.product_uom_qty = 1
        with sale_form.order_line.new() as line:
            line.product_id = cls.smallCabinet
            line.product_uom_qty = 1
        with sale_form.order_line.new() as line:
            line.product_id = cls.roundtable
            line.product_uom_qty = 1
        cls.order = sale_form.save()
        cls.env.user.write(
            {"groups_id": [(4, cls.env.ref("product.group_discount_per_so_line").id)]}
        )

    def test_program_reward_discount_line_with_domain_matching(self):
        """
        Test program with reward type is `discount_line` for domain matching of product
        """
        program_form = Form(
            self.env["coupon.program"],
            view="sale_coupon.sale_coupon_program_view_promo_program_form",
        )
        program_form.name = (
            '10% reduction if the name of the product contains "Cabinet"'
        )
        program_form.promo_code_usage = "no_code_needed"
        program_form.reward_type = "discount_line"
        program_form.discount_type = "percentage"
        program_form.discount_percentage = 10.0
        program_form.rule_products_domain = "[('name', 'ilike', 'Cabinet')]"
        program_form.discount_apply_on = "specific_products"
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
        # Check amount total after apply coupon: 300-(50+100)*0.1
        self.assertEqual(
            self.order.amount_total,
            285.0,
            "The order total with programs should be 285.00",
        )
        self.assertEqual(
            self.order.order_line.filtered(
                lambda line: line.product_id == self.largeCabinet
            ).discount,
            10,
            "The discount for Large Cabinet should be 10%",
        )
        self.assertEqual(
            self.order.order_line.filtered(
                lambda line: line.product_id == self.smallCabinet
            ).discount,
            10,
            "The discount for Small Cabinet should be 10%",
        )
