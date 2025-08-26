# Copyright 2023 Tecnativa - Pilar Vargas
# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class TestLoyaltyPartnerApplicabilityCase(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disable sharing of coupons between members of the same trading entity
        cls.env["ir.config_parameter"].set_param("allow_coupon_sharing", "False")
        product_obj = cls.env["product.product"]
        partner_obj = cls.env["res.partner"]
        cls.commercial_entity = cls.env["res.partner"].create(
            {"name": "Mr. Commercial Entity"}
        )
        cls.product_a = product_obj.create({"name": "Product A", "list_price": 50})
        cls.product_b = product_obj.create({"name": "Product B", "list_price": 10})
        cls.product_c = product_obj.create({"name": "Product C", "list_price": 70})
        cls.partner1 = partner_obj.create(
            {"name": "Mr. Partner One", "parent_id": cls.commercial_entity.id}
        )
        cls.partner2 = partner_obj.create(
            {"name": "Mr. Partner Two", "parent_id": cls.commercial_entity.id}
        )
        cls.partner3 = partner_obj.create({"name": "Mr. Partner Three"})
        cls.program_no_restriction = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Program Restricted to Partner ids",
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
                            "required_points": 1,
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )
        cls.program_restricted_to_partner_ids = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Program Restricted to Partner ids",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "partner_ids": [Command.link(cls.partner1.id)],
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
                            "required_points": 1,
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )
        cls.program_restricted_to_partner_domain = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Program Restricted to Partner Domain",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "partner_domain": "[('id', '=', %s)]" % cls.partner2.id,
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
                            "required_points": 1,
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )
        cls.program_restricted_to_partner_domain_and_partner_ids = cls.env[
            "loyalty.program"
        ].create(
            {
                "name": "Test Loyalty Program Restricted to Partner Domain and Partner ids",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "partner_ids": [Command.link(cls.partner1.id)],
                "partner_domain": "[('id', '=', %s)]" % cls.partner2.id,
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
                            "required_points": 1,
                            "discount": 10,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ],
            }
        )
        cls.promotion_program = cls.env["loyalty.program"].create(
            {
                "name": "Test Promotions Sale Loyalty Partner Applicability",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "partner_domain": [
                    "|",
                    ("id", "=", cls.partner1.id),
                    ("id", "=", cls.partner2.id),
                ],
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    ),
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    ),
                ],
                "reward_ids": [
                    Command.create(
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
        cls.promo_code_program = cls.env["loyalty.program"].create(
            {
                "name": "Test Discount Code Sale Loyalty Partner Applicability",
                "program_type": "promo_code",
                "trigger": "with_code",
                "applies_on": "current",
                "partner_domain": [
                    "|",
                    ("id", "=", cls.partner1.id),
                    ("id", "=", cls.partner2.id),
                ],
                "rule_ids": [
                    Command.create(
                        {
                            "code": "10DISCOUNT",
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    ),
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    ),
                ],
                "reward_ids": [
                    Command.create(
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
        cls.next_order_coupon = cls.env["loyalty.program"].create(
            {
                "name": "Test Loyalty Limit Next Order Coupons",
                "program_type": "next_order_coupons",
                "trigger": "auto",
                "applies_on": "future",
                "partner_domain": [("id", "=", cls.partner1.id)],
                "rule_ids": [
                    Command.create(
                        {
                            "reward_point_mode": "order",
                            "minimum_qty": 1,
                        },
                    ),
                ],
                "reward_ids": [
                    Command.create(
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
