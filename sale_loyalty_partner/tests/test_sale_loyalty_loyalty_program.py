# Copyright 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class TestLoyaltyProgramPartner(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test partner
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "email": "test@example.com",
            }
        )

        # Create loyalty program
        cls.loyalty_program = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Program",
                "partner_id": cls.partner.id,
                "program_type": "promotion",
                "applies_on": "current",
                "trigger": "auto",
            }
        )

        # Create coupon linked to loyalty program
        cls.program_coupon = cls.env["loyalty.card"].create(
            {
                "program_id": cls.loyalty_program.id,
                "partner_id": cls.partner.id,
                "points": 10,
            }
        )

        # Create test product
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 100.0,
            }
        )

        # Create sale order
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
            }
        )
        cls.env["sale.order.line"].create(
            {
                "order_id": cls.sale_order.id,
                "product_id": cls.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
            }
        )

        # Apply coupon to the sale order
        cls.sale_order.write(
            {"applied_coupon_ids": [Command.link(cls.program_coupon.id)]}
        )

    def _get_sale_report_data(self, sale_order):
        """Helper method to get sale report data after ensuring it's up to date."""
        self.env.flush_all()
        self.env.invalidate_all()

        return self.env["sale.report"].search(
            [
                ("name", "=", sale_order.name),
                ("partner_id", "=", sale_order.partner_id.id),
            ]
        )

    def test_loyalty_program_partner(self):
        """Test that the loyalty program partner is set correctly."""
        self.assertEqual(
            self.loyalty_program.partner_id,
            self.partner,
            "Partner should be correctly set on loyalty program",
        )

    def test_sale_report_includes_coupon(self):
        """Test that the sale report includes applied coupon data."""
        # Confirm sale order
        self.sale_order.action_confirm()

        # Get sale report data
        report_data = self._get_sale_report_data(self.sale_order)

        self.assertTrue(report_data, "Sale report data should be created")
        self.assertIn(
            self.program_coupon.id,
            self.sale_order.applied_coupon_ids.ids,
            "Coupon should be applied to the sale order",
        )

    def test_sale_report_no_coupon(self):
        """Test sale report when no coupon is applied."""
        # Create another sale order without a coupon
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
            }
        )

        # Confirm sale order
        sale_order.action_confirm()

        # Get sale report data
        report_data = self._get_sale_report_data(sale_order)

        self.assertTrue(report_data, "Sale report data should be created")
        self.assertFalse(
            sale_order.applied_coupon_ids,
            "No coupon should be applied to the sale order",
        )
