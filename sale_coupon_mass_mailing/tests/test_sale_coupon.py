# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestSaleCoupon(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env["res.partner"].create({"name": "Test Partner 1"})
        cls.partner_2 = cls.env["res.partner"].create({"name": "Test Partner 2"})
        cls.program_all_partners = cls.env["sale.coupon.program"].create(
            {"name": "Test program all partners"}
        )
        cls.program_custom_partners = cls.env["sale.coupon.program"].create(
            {
                "name": "Test program custom partners",
                "rule_partners_domain": [("id", "=", cls.partner_1.id)],
            }
        )

    def test_program_all_partners(self):
        self.assertEqual(self.program_all_partners.mailing_count, 0)
        self.program_all_partners.action_mailing_count()
        self.assertEqual(self.program_all_partners.mailing_count, 1)
        mailing = self.program_all_partners.mailing_ids.filtered(
            lambda x: x.program_id == self.program_all_partners
        )
        self.assertEqual(mailing, self.program_all_partners.mailing_ids[0])
        self.assertFalse(mailing.mailing_domain)
        self.assertEqual(mailing.subject, self.program_all_partners.name)
        action = self.program_all_partners.action_mailing_count()
        self.assertEqual(
            action["context"]["default_program_id"], self.program_all_partners.id
        )
        self.assertEqual(
            action["context"]["default_subject"], self.program_all_partners.name
        )
        self.assertEqual(self.program_all_partners.mailing_count, 1)

    def test_program_custom_partners(self):
        self.assertEqual(self.program_custom_partners.mailing_count, 0)
        self.program_custom_partners.action_mailing_count()
        self.assertEqual(self.program_custom_partners.mailing_count, 1)
        mailing = self.program_custom_partners.mailing_ids.filtered(
            lambda x: x.program_id == self.program_custom_partners
        )
        self.assertEqual(mailing, self.program_custom_partners.mailing_ids[0])
        self.assertEqual(
            mailing.mailing_domain, self.program_custom_partners.rule_partners_domain
        )
        self.assertEqual(mailing.subject, self.program_custom_partners.name)
        action = self.program_custom_partners.action_mailing_count()
        self.assertEqual(
            action["context"]["default_program_id"], self.program_custom_partners.id
        )
        self.assertEqual(
            action["context"]["default_subject"], self.program_custom_partners.name
        )
        self.assertEqual(self.program_custom_partners.mailing_count, 1)
