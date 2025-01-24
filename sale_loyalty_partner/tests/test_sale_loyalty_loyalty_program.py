# Copyright 2025 BhaveshHeliconia
# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestLoyaltyProgramPartner(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.loyalty_program_a = cls._create_loyalty_program()
        cls.loyalty_program_b = cls._create_loyalty_program()
        cls.loyalty_program_b.partner_id = cls.partner
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "consu"}
        )
        cls.order_a = cls._create_sale_order(cls.loyalty_program_a)
        cls.order_b = cls._create_sale_order(cls.loyalty_program_b)

    @classmethod
    def _create_loyalty_program(cls):
        return cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Program 10% auto",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    )
                ],
                "reward_ids": [
                    Command.create(
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

    @classmethod
    def _create_sale_order(cls, loyalty_program):
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product
        sale = sale_form.save()
        sale._update_programs_and_rewards()
        wizard = (
            cls.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=sale)
            .create({"selected_reward_id": loyalty_program.reward_ids.id})
        )
        wizard.action_apply()
        return sale

    def test_sale_order_misc(self):
        order_lines = (self.order_a + self.order_b).order_line.filtered(
            "is_reward_line"
        )
        report_data = self.env["sale.report"].search([("id", "in", order_lines.ids)])
        report_data_a = report_data.filtered(lambda x: x.name == self.order_a.name)
        self.assertFalse(report_data_a.loyalty_program_partner_id)
        report_data_b = report_data.filtered(lambda x: x.name == self.order_b.name)
        self.assertEqual(report_data_b.loyalty_program_partner_id, self.partner)
