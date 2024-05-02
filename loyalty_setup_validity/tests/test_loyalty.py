from freezegun import freeze_time

from odoo import fields
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestLoyalty(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.program = cls.env["loyalty.program"].create(
            {
                "name": "Test Program",
                "reward_ids": [
                    Command.create(
                        {
                            "description": "Test Product",
                        }
                    ),
                ],
                "validity_type": "after_activation",
                "validity_duration": 30,
            }
        )

    @freeze_time("2024-04-25")
    def test_validity_duration(self):
        card = self.env["loyalty.card"].create(
            {
                "program_id": self.program.id,
            }
        )
        self.assertEqual(card.expiration_date, fields.Date.from_string("2024-05-25"))

    @freeze_time("2024-04-25")
    def test_fixed(self):
        self.program.validity_type = "fixed"
        self.program.date_to = fields.Date.from_string("2024-05-01")
        card = self.env["loyalty.card"].create(
            {
                "program_id": self.program.id,
            }
        )
        self.assertEqual(card.expiration_date, fields.Date.from_string("2024-05-01"))
