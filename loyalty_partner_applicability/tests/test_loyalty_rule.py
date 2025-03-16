# Copyright 2025 Kencove - Mohamed Alkobrosli
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestLoyalty(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Loyalty_Program = cls.env["loyalty.program"].create(
            {
                "name": "10% discount",
                "program_type": "coupons",
            }
        )
        cls.Loyalty_Generate_Wizard = cls.env["loyalty.generate.wizard"].create(
            {
                "program_id": cls.Loyalty_Program.id,
                "coupon_qty": 5,
                "mode": "anonymous",
            }
        )
        cls.Loyalty_Rule = cls.env["loyalty.rule"].create(
            {
                "program_id": cls.Loyalty_Program.id,
                "minimum_amount_tax_mode": "incl",
            }
        )

    def test_generate_coupons(self):
        self.assertFalse(self.Loyalty_Program.coupon_ids)
        is_succeeded = self.Loyalty_Generate_Wizard.generate_coupons()
        self.assertTrue(is_succeeded)
        self.assertEqual(len(self.Loyalty_Program.coupon_ids), 5)

    def test_partner_related_domains(self):
        self.assertEqual(self.Loyalty_Rule.rule_partners_domain, "[]")
        self.Loyalty_Rule.rule_partners_domain = "[('name', 'ilike', 'Azure')]"
        self.assertEqual(
            self.Loyalty_Rule.rule_partners_domain, "[('name', 'ilike', 'Azure')]"
        )
