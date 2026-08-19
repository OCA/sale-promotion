# Copyright 2020-2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.loyalty_partner_applicability.tests.common import (
    TestLoyaltyPartnerApplicabilityCase,
)


class TestLoyaltyMassMailing(TestLoyaltyPartnerApplicabilityCase):
    def _test_program_mass_mailing(self, program):
        self.assertEqual(program.mailing_count, 0)
        program.action_mailing_count()
        self.assertEqual(program.mailing_count, 1)
        mailing = program.mailing_ids.filtered(lambda x: x.program_id == program)
        self.assertEqual(mailing, program.mailing_ids[0])
        self.assertEqual(mailing.mailing_domain, program.partner_domain)
        self.assertEqual(mailing.subject, program.name)
        action = program.action_mailing_count()
        self.assertEqual(action["context"]["default_program_id"], program.id)
        self.assertEqual(action["context"]["default_subject"], program.name)
        self.assertEqual(program.mailing_count, 1)

    def test_program_no_restriction(self):
        self._test_program_mass_mailing(self.program_no_restriction)

    def test_program_restricted_to_partner_ids(self):
        self._test_program_mass_mailing(self.program_restricted_to_partner_ids)

    def test_program_restricted_to_partner_domain(self):
        self._test_program_mass_mailing(self.program_restricted_to_partner_domain)

    def test_program_restricted_to_partner_domain_and_partner_ids(self):
        self._test_program_mass_mailing(
            self.program_restricted_to_partner_domain_and_partner_ids
        )

    def test_promotion_program(self):
        self._test_program_mass_mailing(self.promotion_program)

    def test_promo_code_program(self):
        self._test_program_mass_mailing(self.promo_code_program)

    def test_next_order_coupon(self):
        self._test_program_mass_mailing(self.next_order_coupon)
