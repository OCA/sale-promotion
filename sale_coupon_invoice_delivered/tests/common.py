from odoo.addons.sale_coupon.tests.common import TestSaleCouponCommon


class TestSaleCouponInvoiceDeliveredCommon(TestSaleCouponCommon):
    def setUp(self):
        super(TestSaleCouponInvoiceDeliveredCommon, self).setUp()

        self.largeCabinet = self.env["product.product"].create(
            {
                "name": "Large Cabinet",
                "list_price": 320.0,
                "taxes_id": False,
            }
        )
        self.conferenceChair = self.env["product.product"].create(
            {
                "name": "Conference Chair",
                "list_price": 16.5,
                "taxes_id": False,
            }
        )

        self.drawerBlack = self.env["product.product"].create(
            {
                "name": "Drawer Black",
                "list_price": 25.0,
                "taxes_id": False,
            }
        )

        self.steve = self.env["res.partner"].create(
            {
                "name": "Steve Bucknor",
                "email": "steve.bucknor@example.com",
            }
        )
        self.empty_order = self.env["sale.order"].create({"partner_id": self.steve.id})

        self.global_promo = self.env["coupon.program"].create(
            {
                "name": "10% on all orders",
                "promo_code_usage": "no_code_needed",
                "discount_type": "percentage",
                "discount_percentage": 10.0,
                "program_type": "promotion_program",
                "sequence": 20,
            }
        )

        self.global_promo.invoice_on_delivered = True
