# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import TestLoyaltyPartnerApplicabilityCase


class TestLoyaltyPartnerApplicability(TestLoyaltyPartnerApplicabilityCase):
    def _assertCheckValidPartner(self, program, partner, expected):
        self.assertEqual(
            program._is_partner_valid(partner),
            expected,
            f"Partner {partner.name} should be {'valid' if expected else 'invalid'} "
            f"for program {program.name} (_is_partner_valid)",
        )
        domain = program._get_partner_domain(partner)
        is_valid = partner.search_count(domain) > 0
        self.assertEqual(
            is_valid,
            expected,
            f"Partner {partner.name} should be {'valid' if expected else 'invalid'} "
            f"for program {program.name} (_get_partner_domain)",
        )

    def test_program_no_restriction(self):
        program = self.program_no_restriction
        self.assertFalse(program._is_coupon_sharing_allowed())
        self.assertFalse(program._is_coupon_sharing_allowed())
        self._assertCheckValidPartner(program, self.partner1, True)
        self._assertCheckValidPartner(program, self.partner2, True)
        self._assertCheckValidPartner(program, self.partner3, True)

    def test_restriction_on_partner_ids(self):
        program = self.program_restricted_to_partner_ids
        self.assertFalse(program._is_coupon_sharing_allowed())
        self._assertCheckValidPartner(program, self.partner1, True)
        self._assertCheckValidPartner(program, self.partner2, False)
        self._assertCheckValidPartner(program, self.partner3, False)

    def test_restriction_on_partner_domain(self):
        program = self.program_restricted_to_partner_domain
        self.assertFalse(program._is_coupon_sharing_allowed())
        self._assertCheckValidPartner(program, self.partner1, False)
        self._assertCheckValidPartner(program, self.partner2, True)
        self._assertCheckValidPartner(program, self.partner3, False)

    def test_restriction_on_partner_domain_and_partner_ids(self):
        program = self.program_restricted_to_partner_domain_and_partner_ids
        self.assertFalse(program._is_coupon_sharing_allowed())
        self._assertCheckValidPartner(program, self.partner1, True)
        self._assertCheckValidPartner(program, self.partner2, True)
        self._assertCheckValidPartner(program, self.partner3, False)
