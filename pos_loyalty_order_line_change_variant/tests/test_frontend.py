# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.test_frontend import TestPointOfSaleHttpCommon


@tagged("post_install", "-at_install")
class TestUi(TestPointOfSaleHttpCommon):
    def test_change_variant_removes_reward(self):
        self.env["loyalty.program"].search([]).write({"active": False})
        size = self.env["product.attribute"].create(
            {
                "name": "Size",
                "create_variant": "always",
                "value_ids": [
                    Command.create({"name": "Large", "sequence": 1}),
                    Command.create({"name": "Regular", "sequence": 2}),
                ],
            }
        )
        tea = self.env["product.template"].create(
            {
                "name": "Tea",
                "list_price": 300,
                "taxes_id": False,
                "available_in_pos": True,
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": size.id,
                            "value_ids": [Command.set(size.value_ids.ids)],
                        }
                    )
                ],
            }
        )
        large_tea = tea.product_variant_ids.filtered(
            lambda p: p.product_template_variant_value_ids.name == "Large"
        )
        bottle = self.env["product.product"].create(
            {
                "name": "Own Bottle",
                "list_price": 0,
                "taxes_id": False,
                "available_in_pos": True,
            }
        )
        self.env["loyalty.program"].create(
            {
                "name": "Own Bottle",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "rule_ids": [
                    Command.create(
                        {
                            "product_ids": [Command.set(bottle.ids)],
                            "reward_point_mode": "unit",
                            "reward_point_amount": 1,
                        }
                    )
                ],
                "reward_ids": [
                    Command.create(
                        {
                            "reward_type": "discount",
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "specific",
                            "discount_product_ids": [Command.set(large_tea.ids)],
                            "required_points": 1,
                            "description": "Large discount",
                        }
                    )
                ],
            }
        )
        self.main_pos_config.write(
            {"tax_regime_selection": False, "use_pricelist": False}
        )
        self.main_pos_config.with_user(self.pos_user).open_ui()
        self.main_pos_config.current_session_id.set_opening_control(0, "")
        self.start_tour(
            f"/pos/ui?config_id={self.main_pos_config.id}",
            "PosLoyaltyOrderLineChangeVariantTour",
            login="pos_user",
        )
