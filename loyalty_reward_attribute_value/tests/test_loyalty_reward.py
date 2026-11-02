# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestLoyaltyRewardAttributeValue(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.attribute = cls.env["product.attribute"].create(
            {
                "name": "Size",
                "create_variant": "no_variant",
                "value_ids": [
                    Command.create({"name": "Small"}),
                    Command.create({"name": "Large"}),
                ],
            }
        )
        cls.large = cls.attribute.value_ids.filtered(lambda v: v.name == "Large")
        cls.template = cls.env["product.template"].create(
            {
                "name": "Drink",
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": cls.attribute.id,
                            "value_ids": [Command.set(cls.attribute.value_ids.ids)],
                        }
                    )
                ],
            }
        )
        cls.program = cls.env["loyalty.program"].create(
            {
                "name": "Own cup",
                "program_type": "promotion",
                "reward_ids": [
                    Command.create(
                        {
                            "reward_type": "discount",
                            "discount": 100,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        }
                    )
                ],
            }
        )
        cls.reward = cls.program.reward_ids

    def test_discount_ptav_ids(self):
        self.assertFalse(self.reward.discount_ptav_ids)
        self.reward.discount_attribute_value_ids = self.large
        ptav = self.template.attribute_line_ids.product_template_value_ids.filtered(
            lambda v: v.product_attribute_value_id == self.large
        )
        self.assertEqual(self.reward.discount_ptav_ids, ptav)

    def test_cheapest_not_allowed(self):
        self.reward.discount_attribute_value_ids = self.large
        with self.assertRaises(ValidationError):
            self.reward.discount_applicability = "cheapest"
