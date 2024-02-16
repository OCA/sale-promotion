# Copyright 2024 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("-at_install", "post_install")
class LoyaltyInitialDateValidity(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        loyalty_program = cls.env["loyalty.program"]
        # Promotion with start date currently valid
        cls.promotion = loyalty_program.create(
            {
                "name": "Test loyalty initial date validity",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "date_from": "2024-02-14",
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
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )

    @freeze_time("2024-02-15")
    def test_01_check_date_from_date_to(self):
        self.assertFalse(self.promotion.date_to)
        # The end date cannot be earlier than the start date.
        with self.assertRaises(UserError):
            self.promotion.date_to = "2024-02-07"
        self.promotion.date_to = "2024-02-25"
        self.assertTrue(self.promotion.date_to)
        # If there is no start date there is no restriction on the end date.
        self.promotion.date_from = False
        self.promotion.date_to = "2024-02-07"
