from odoo.tests import Form, common, tagged


@tagged("post_install", "-at_install")
class TestDeliveryAutoRefresh(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        service = cls.env["product.product"].create(
            {"name": "Service Test", "type": "service"}
        )
        pricelist = cls.env["product.pricelist"].create(
            {"name": "Test pricelist", "currency_id": cls.env.company.currency_id.id}
        )
        carrier_form = Form(cls.env["delivery.carrier"])
        carrier_form.name = "Test carrier"
        carrier_form.delivery_type = "fixed"
        carrier_form.product_id = service
        carrier_form.fixed_price = 10
        cls.carrier = carrier_form.save()
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "list_price": 20}
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "property_delivery_carrier_id": cls.carrier.id,
                "property_product_pricelist": pricelist.id,
            }
        )
        cls.env["ir.config_parameter"].sudo().set_param(
            "delivery_auto_refresh.set_default_carrier", 1
        )
        cls.env["ir.config_parameter"].sudo().set_param(
            "delivery_auto_refresh.auto_add_delivery_line", 1
        )
        coupon_program_form = Form(
            cls.env["coupon.program"],
            view="sale_coupon.sale_coupon_program_view_promo_program_form",
        )
        coupon_program_form.name = "Test Free Shipping Program"
        coupon_program_form.promo_code_usage = "no_code_needed"
        coupon_program_form.rule_minimum_amount = 100
        cls.coupon_program = coupon_program_form.save()
        cls.coupon_program.company_id.auto_refresh_coupon = True

    def test_sale_coupon_delivery_auto_refresh(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        order_form.partner_invoice_id = self.partner
        order_form.partner_shipping_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 2
            line_form.price_unit = 150
        self.order = order_form.save()
        self.assertTrue(self.order.order_line.filtered("is_reward_line"))
        self.assertTrue(self.order.order_line.filtered("is_delivery"))
