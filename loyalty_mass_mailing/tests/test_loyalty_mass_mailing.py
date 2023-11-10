# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestLoyaltyMassMailing(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner1 = cls.env["res.partner"].create({"name": "Test Partner 1"})
        cls.partner2 = cls.env["res.partner"].create({"name": "Test Partner 2"})
        # Program without defined partner domain rules
        cls.program_all_partners = cls.env["loyalty.program"].create(
            {
                "name": "Test program all partners",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    )
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "discount",
                            "required_points": 1,
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )
        # Program with domain defined in one rule and not in the other
        cls.program_all_partners_2 = cls.env["loyalty.program"].create(
            {
                "name": "Test program all partners",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "rule_partners_domain": [("id", "=", cls.partner1.id)],
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    ),
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "discount",
                            "required_points": 1,
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )
        # Program with all partner domain rules defined
        cls.program_custom_partners = cls.env["loyalty.program"].create(
            {
                "name": "Test program custom partners",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "rule_partners_domain": [("id", "=", cls.partner1.id)],
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "rule_partners_domain": [("id", "=", cls.partner2.id)],
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    ),
                ],
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "discount",
                            "required_points": 1,
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )

    def test_program_all_partners(self):
        # When there is no domain for partners defined in any rule, then the
        # mailing_domain will be = [ ].
        self.assertEqual(self.program_all_partners.mailing_count, 0)
        self.program_all_partners.action_mailing_count()
        self.assertEqual(self.program_all_partners.mailing_count, 1)
        mailing = self.program_all_partners.mailing_ids.filtered(
            lambda x: x.program_id == self.program_all_partners
        )
        self.assertEqual(mailing, self.program_all_partners.mailing_ids[0])
        self.assertFalse(mailing.mailing_domain != "[]")
        self.assertEqual(mailing.subject, self.program_all_partners.name)
        action = self.program_all_partners.action_mailing_count()
        self.assertEqual(
            action["context"]["default_program_id"], self.program_all_partners.id
        )
        self.assertEqual(
            action["context"]["default_subject"], self.program_all_partners.name
        )
        self.assertEqual(self.program_all_partners.mailing_count, 1)

    def test_program_all_partners_2(self):
        # Cuando hay varias reglas y en alguna no está definido el dominio para
        # partners, entonces el mailing_domain será = [ ]
        self.assertEqual(self.program_all_partners_2.mailing_count, 0)
        self.program_all_partners_2.action_mailing_count()
        self.assertEqual(self.program_all_partners_2.mailing_count, 1)
        mailing = self.program_all_partners_2.mailing_ids.filtered(
            lambda x: x.program_id == self.program_all_partners_2
        )
        self.assertEqual(mailing, self.program_all_partners_2.mailing_ids[0])
        self.assertFalse(mailing.mailing_domain != "[]")
        self.assertEqual(mailing.subject, self.program_all_partners_2.name)
        action = self.program_all_partners_2.action_mailing_count()
        self.assertEqual(
            action["context"]["default_program_id"], self.program_all_partners_2.id
        )
        self.assertEqual(
            action["context"]["default_subject"], self.program_all_partners_2.name
        )
        self.assertEqual(self.program_all_partners_2.mailing_count, 1)

    def test_program_custom_partners(self):
        # When all the rules have the domain for partners defined, then the
        # mailing_domain will be the combination of all those domains.
        self.assertEqual(self.program_custom_partners.mailing_count, 0)
        self.program_custom_partners.action_mailing_count()
        self.assertEqual(self.program_custom_partners.mailing_count, 1)
        mailing = self.program_custom_partners.mailing_ids.filtered(
            lambda x: x.program_id == self.program_custom_partners
        )
        self.assertEqual(mailing, self.program_custom_partners.mailing_ids[0])
        self.assertEqual(
            mailing.mailing_domain,
            self.program_custom_partners.partner_applicability_domain,
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
