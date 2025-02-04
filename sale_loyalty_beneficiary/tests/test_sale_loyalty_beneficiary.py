# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.sale_loyalty.tests.common import TestSaleCouponCommon


class TestSaleLoyaltyBeneficiary(TestSaleCouponCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.commercial_partner = cls.env["res.partner"].create(
            {
                "name": "Commercial Partner",
                "is_company": True,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "parent_id": cls.commercial_partner.id,
            }
        )
        cls.invoiced_partner = cls.env["res.partner"].create(
            {
                "name": "Invoiced Partner",
            }
        )
        cls.loyalty_program = cls.env["loyalty.program"].create(
            {
                "name": "Loyalty Program",
                "program_type": "loyalty",
                "trigger": "auto",
                "applies_on": "both",
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "unit",
                            "reward_point_amount": 1,
                            "product_ids": [cls.product_a.id],
                        }
                    )
                ],
                "reward_ids": [
                    Command.create(
                        {
                            "reward_type": "discount",
                            "discount": 1.5,
                            "discount_mode": "per_point",
                            "discount_applicability": "order",
                            "required_points": 1,
                        }
                    )
                ],
            }
        )

    def _makes_and_confirm_order(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "partner_invoice_id": self.invoiced_partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "product_uom_qty": 1,
                        }
                    )
                ],
            }
        )
        order.action_confirm()
        return order

    def _get_cart(self, partner):
        self.loyalty_program.invalidate_recordset(["coupon_ids"])
        return self.loyalty_program.coupon_ids.filtered(
            lambda c: c.partner_id == partner
        )

    def test_beneficiary_partner(self):
        self.loyalty_program.beneficiary_partner_type = "partner"
        self.assertFalse(self._get_cart(self.partner))
        self._makes_and_confirm_order()
        cart = self._get_cart(self.partner)
        self.assertTrue(cart)
        self.assertEqual(cart.points, 1)
        self._makes_and_confirm_order()
        self.assertEqual(cart.points, 2)

    def test_beneficiary_invoiced_partner(self):
        self.loyalty_program.beneficiary_partner_type = "invoiced_partner"
        self.assertFalse(self._get_cart(self.invoiced_partner))
        self._makes_and_confirm_order()
        cart = self._get_cart(self.invoiced_partner)
        self.assertTrue(cart)
        self.assertEqual(cart.points, 1)
        self._makes_and_confirm_order()
        self.assertEqual(cart.points, 2)

    def test_beneficiary_commercial_entity(self):
        self.loyalty_program.beneficiary_partner_type = "commercial_entity"
        self.assertFalse(self._get_cart(self.commercial_partner))
        self._makes_and_confirm_order()
        cart = self._get_cart(self.commercial_partner)
        self.assertTrue(cart)
        self.assertEqual(cart.points, 1)
        self._makes_and_confirm_order()
        self.assertEqual(cart.points, 2)
