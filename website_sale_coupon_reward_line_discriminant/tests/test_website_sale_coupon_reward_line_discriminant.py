from odoo.tests import Form, common

from odoo.addons.website.tools import MockRequest
from odoo.addons.website_sale_coupon.controllers.main import WebsiteSale


class TestWebsiteSaleCouponReward(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_a = cls.env["product.product"].create(
            {"name": "Product A", "sale_ok": True, "list_price": 50}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Product B", "sale_ok": True, "list_price": 60}
        )
        coupon_program_form = Form(
            cls.env["sale.coupon.program"],
            view="sale_coupon.sale_coupon_program_view_promo_program_form",
        )
        coupon_program_form.name = "Test Line Discriminant Program"
        coupon_program_form.promo_code_usage = "no_code_needed"
        coupon_program_form.reward_type = "multi_gift"
        coupon_program_form.rule_products_domain = (
            "[('id', '=', %s)]" % cls.product_a.id
        )
        with coupon_program_form.coupon_multi_gift_ids.new() as reward_line:
            reward_line.reward_product_ids.add(cls.product_b)
            reward_line.reward_product_quantity = 2
        cls.coupon_program = coupon_program_form.save()
        cls.website = cls.env["website"].search([], limit=1)

    @classmethod
    def _create_sale(cls, website=False):
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
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_a
            line_form.product_uom_qty = 1
        sale = sale_form.save()
        sale.website_id = website
        return sale


class TestWebsiteSaleCouponRewardLineDiscriminant(TestWebsiteSaleCouponReward):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.WebsiteSaleController = WebsiteSale()

    def test_website_sale_coupon_reward_line_discriminant(self):
        website_sale = self._create_sale(self.website)
        with MockRequest(self.env, website=self.website, sale_order_id=website_sale.id):
            self.WebsiteSaleController.cart_update(self.product_b)
            lines_b = website_sale.order_line.filtered(
                lambda x: x.product_id == self.product_b
            )
            self.assertFalse(lines_b[-1].is_reward_line)
