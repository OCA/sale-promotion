# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common


class TestWebsiteSaleCouponAutorefresh(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
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
        cls.product = cls.env["product.product"].create({"name": "Test"})
        coupon_program_form = Form(
            cls.env["coupon.program"],
            view="sale_coupon.sale_coupon_program_view_promo_program_form",
        )
        coupon_program_form.name = "Test Discount Program"
        coupon_program_form.promo_code_usage = "no_code_needed"
        coupon_program_form.discount_type = "percentage"
        coupon_program_form.discount_percentage = 50
        coupon_program_form.discount_apply_on = "on_order"
        coupon_program_form.rule_minimum_amount = 100
        cls.coupon_program = coupon_program_form.save()
        cls.coupon_program.company_id.auto_refresh_coupon = True

    def test_sale_coupon_auto_refresh_on_create(self):
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1
            line_form.price_unit = 150
        sale = sale_form.save()
        discount_line = sale.order_line.filtered("is_reward_line")
        self.assertAlmostEqual(-75, discount_line.price_unit)

    def test_sale_coupon_auto_refresh_on_update(self):
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1
            line_form.price_unit = 1
        sale = sale_form.save()
        discount_line = sale.order_line.filtered("is_reward_line")
        self.assertFalse(bool(discount_line))
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 200
        sale_form.save()
        discount_line = sale.order_line.filtered("is_reward_line")
        self.assertEqual(1, len(discount_line))
        self.assertAlmostEqual(-100.5, discount_line.price_unit)
