# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestSaleCoupon(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env["res.partner"].create({"name": "Test Partner 1"})
        cls.partner_2 = cls.env["res.partner"].create({"name": "Test Partner 2"})
        cls.program_all_partners = cls.env["loyalty.program"].create(
            {
                "name": "Test program all partners",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_point_mode": "unit",
                            "rule_partners_domain": [],
                        },
                    )
                ],
            }
        )
        cls.program_custom_partners = cls.env["loyalty.program"].create(
            {
                "name": "Test program custom partners",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_point_mode": "unit",
                            "rule_partners_domain": [("id", "=", cls.partner_1.id)],
                        },
                    )
                ],
            }
        )

    def test_program_all_partners(self):
        self.assertEqual(self.program_all_partners.rule_ids[0].mailing_count, 0)
        self.program_all_partners.rule_ids[0].action_mailing_count()
        self.assertEqual(self.program_all_partners.rule_ids[0].mailing_count, 1)
        mailing = self.program_all_partners.rule_ids[0].mailing_ids.filtered(
            lambda x: x.rule_id == self.program_all_partners.rule_ids[0]
        )
        self.assertEqual(mailing, self.program_all_partners.rule_ids[0].mailing_ids[0])
        self.assertEqual("[('is_blacklisted', '=', False)]", mailing.mailing_domain)
        self.assertEqual(mailing.subject, self.program_all_partners.name)
        action = self.program_all_partners.rule_ids[0].action_mailing_count()
        self.assertEqual(
            action["context"]["default_rule_id"],
            self.program_all_partners.rule_ids[0].id,
        )
        self.assertEqual(
            action["context"]["default_subject"], self.program_all_partners.name
        )
        self.assertEqual(self.program_all_partners.rule_ids[0].mailing_count, 1)

    def test_program_custom_partners(self):
        self.assertEqual(self.program_custom_partners.rule_ids[0].mailing_count, 0)
        self.program_custom_partners.rule_ids[0].action_mailing_count()
        self.assertEqual(self.program_custom_partners.rule_ids[0].mailing_count, 1)
        mailing = self.program_custom_partners.rule_ids[0].mailing_ids.filtered(
            lambda x: x.rule_id == self.program_custom_partners.rule_ids[0]
        )
        self.assertEqual(
            mailing, self.program_custom_partners.rule_ids[0].mailing_ids[0]
        )

        self.assertEqual(mailing.subject, self.program_custom_partners.name)
        action = self.program_custom_partners.rule_ids[0].action_mailing_count()
        self.assertEqual(
            action["context"]["default_rule_id"],
            self.program_custom_partners.rule_ids[0].id,
        )
        self.assertEqual(
            action["context"]["default_subject"], self.program_custom_partners.name
        )
        self.assertEqual(self.program_custom_partners.rule_ids[0].mailing_count, 1)
