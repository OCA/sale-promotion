# Copyright 2022 Ooops404
# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class CouponDomainProductDiscount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        product_obj = cls.env["product.product"]
        cls.largeCabinet = product_obj.create(
            {"name": "Large Cabinet", "list_price": 50.0, "taxes_id": False}
        )
        cls.conferenceChair = product_obj.create(
            {"name": "Conference Chair", "list_price": 100, "taxes_id": False}
        )
        cls.pedalBin = product_obj.create(
            {"name": "Pedal Bin", "list_price": 150, "taxes_id": False}
        )
        cls.drawerBlack = product_obj.create(
            {"name": "Drawer Black", "list_price": 200, "taxes_id": False}
        )
        cls.steve = cls.env["res.partner"].create(
            {"name": "Steve Bucknor", "email": "steve.bucknor@example.com"}
        )
        cls.percent_tax = cls.env["account.tax"].create(
            {
                "name": "15% Tax",
                "amount_type": "percent",
                "amount": 15,
                "price_include": True,
            }
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
