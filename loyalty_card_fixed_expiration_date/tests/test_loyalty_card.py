# Copyright 2024 (APSL-Nagarro) - Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo.tests.common import TransactionCase


class TestLoyaltyCard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.program_id = cls.env["loyalty.program"].create(
            {"name": "Test", "duration_days": 30, "program_type": "gift_card"}
        )
        cls.wizard = cls.env["loyalty.generate.wizard"].create(
            {"program_id": cls.program_id.id, "coupon_qty": 1}
        )

    def test_loyalt_card_with_fixed_days(self):
        self.wizard.generate_coupons()
        self.assertEqual(
            self.program_id.coupon_ids[0].expiration_date,
            date.today() + timedelta(days=(self.program_id.duration_days)),
        )

    def test_loyalt_card_without_fixed_days(self):
        self.program_id.write({"duration_days": 0})
        self.wizard.generate_coupons()
        self.assertEqual(self.program_id.coupon_ids[0].expiration_date, False)

    def test_loyalt_card_without_fixed_days_with_exp_date(self):
        self.program_id.write({"duration_days": 0})

        expiration_date = date.today() + timedelta(days=10)
        self.wizard.valid_until = expiration_date
        self.wizard.generate_coupons()
        self.assertEqual(self.program_id.coupon_ids[0].expiration_date, expiration_date)
