# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.test_frontend import TestPointOfSaleHttpCommon


@tagged("post_install", "-at_install")
class TestUi(TestPointOfSaleHttpCommon):
    def _create_drink(self, name, price, create_variant, values):
        attribute = self.env["product.attribute"].create(
            {
                "name": f"{name} Size",
                "create_variant": create_variant,
                "value_ids": [Command.create({"name": v}) for v in values],
            }
        )
        template = self.env["product.template"].create(
            {
                "name": name,
                "list_price": price,
                "taxes_id": False,
                "available_in_pos": True,
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": attribute.id,
                            "value_ids": [Command.set(attribute.value_ids.ids)],
                        }
                    )
                ],
            }
        )
        return template.attribute_line_ids.product_template_value_ids

    def test_attribute_value_reward(self):
        self.env["loyalty.program"].search([]).write({"active": False})
        cup_values = self._create_drink(
            "Cup Drink", 300, "no_variant", ["Small", "Big"]
        )
        variant_values = self._create_drink(
            "Variant Drink", 200, "always", ["Medium", "Large"]
        )
        big = cup_values.filtered(lambda v: v.name == "Big")
        large = variant_values.filtered(lambda v: v.name == "Large")
        big.price_extra = 100
        large.price_extra = 50
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
                            "discount": 100,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                            "required_points": 1,
                            "description": "Free option",
                            "discount_attribute_value_ids": [
                                Command.set(
                                    (
                                        big.product_attribute_value_id
                                        | large.product_attribute_value_id
                                    ).ids
                                )
                            ],
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
            "PosLoyaltyRewardAttributeValueTour",
            login="pos_user",
        )

    def _setup_tea_shop(self, bottle_discount=True):
        self.env["loyalty.program"].search([]).write({"active": False})
        topping = self.env["product.attribute"].create(
            {
                "name": "Topping",
                "create_variant": "no_variant",
                "value_ids": [
                    Command.create({"name": "No topping"}),
                    Command.create({"name": "Tapioca"}),
                ],
            }
        )
        tapioca = topping.value_ids.filtered(lambda v: v.name == "Tapioca")
        templates = self.env["product.template"]
        for name, price in (("Tea", 300), ("Dessert", 200)):
            templates |= self.env["product.template"].create(
                {
                    "name": name,
                    "list_price": price,
                    "taxes_id": False,
                    "available_in_pos": True,
                    "attribute_line_ids": [
                        Command.create(
                            {
                                "attribute_id": topping.id,
                                "value_ids": [Command.set(topping.value_ids.ids)],
                            }
                        )
                    ],
                }
            )
        templates.attribute_line_ids.product_template_value_ids.filtered(
            lambda v: v.product_attribute_value_id == tapioca
        ).price_extra = 100
        tea = templates.filtered(lambda t: t.name == "Tea").product_variant_ids
        bottle = self.env["product.product"].create(
            {
                "name": "Own Bottle",
                "list_price": 0,
                "taxes_id": False,
                "available_in_pos": True,
            }
        )
        rewards = [
            {
                "discount": 100,
                "discount_mode": "percent",
                "description": "Free tapioca",
                "discount_attribute_value_ids": [Command.set(tapioca.ids)],
            },
        ]
        if bottle_discount:
            rewards.append(
                {"discount": 50, "discount_mode": "per_order", "description": "Bottle"}
            )
        for reward_vals in rewards:
            self.env["loyalty.program"].create(
                {
                    "name": reward_vals["description"],
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
                                "discount_applicability": "specific",
                                "discount_product_ids": [Command.set(tea.ids)],
                                "required_points": 1,
                                **reward_vals,
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

    def test_more_bottles_than_drinks(self):
        self._setup_tea_shop(bottle_discount=False)
        self.start_tour(
            f"/pos/ui?config_id={self.main_pos_config.id}",
            "PosLoyaltyRewardAttributeValueBottlesTour",
            login="pos_user",
        )

    def test_reward_only_on_eligible_products(self):
        self._setup_tea_shop()
        self.start_tour(
            f"/pos/ui?config_id={self.main_pos_config.id}",
            "PosLoyaltyRewardAttributeValueEligibleTour",
            login="pos_user",
        )
