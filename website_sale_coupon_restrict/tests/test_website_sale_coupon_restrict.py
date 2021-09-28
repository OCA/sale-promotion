# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import Form, common, tagged

from odoo.addons.website.tools import MockRequest
from odoo.addons.website_sale_coupon.controllers.main import WebsiteSale


class TestWebsiteSaleCouponCase(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({"name": "Test"})
        coupon_program_form = Form(
            cls.env["sale.coupon.program"],
            view="sale_coupon.sale_coupon_program_view_form",
        )
        coupon_program_form.name = "Test Discount Program"
        coupon_program_form.website_only = True
        cls.coupon_program = coupon_program_form.save()
        cls.env["sale.coupon.generate"].with_context(
            active_id=cls.coupon_program.id
        ).create({}).generate_coupon()
        cls.coupon = cls.coupon_program.coupon_ids[0]
        cls.website = cls.env["website"].search([], limit=1)

    @classmethod
    def _create_sale(cls, website=False):
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product
            line_form.product_uom_qty = 1
        sale = sale_form.save()
        sale.website_id = website
        return sale


@tagged("-at_install", "post_install")
class TestWebsiteSaleCouponRestrict(TestWebsiteSaleCouponCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.WebsiteSaleController = WebsiteSale()

    def test_website_sale_coupon_restrict(self):
        """Test the same coupon from backend and frontend"""
        backend_sale = self._create_sale()
        with self.assertRaises(UserError):
            self.env["sale.coupon.apply.code"].with_context(
                active_id=backend_sale.id
            ).create({"coupon_code": self.coupon.code}).process_coupon()
        website_sale = self._create_sale(self.website)
        with MockRequest(self.env, website=self.website, sale_order_id=website_sale.id):
            self.WebsiteSaleController.pricelist(promo=self.coupon.code)
            self.assertTrue(
                bool(website_sale.order_line.filtered("is_reward_line")),
                "We should have the coupon applied to the sale",
            )
