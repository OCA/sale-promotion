from odoo.fields import Command
from odoo.tests import common


class TestRewardValuesDiscount(common.TransactionCase):
    def order_line_dict(self, product, qty=1):
        return {
            "name": product.name,
            "product_id": product.id,
            "product_uom_qty": qty,
            "product_uom": product.uom_id.id,
            "price_unit": 10.0,
        }

    def setUp(self):
        super().setUp()

        LoyaltyProgram = self.env["loyalty.program"]
        LoyaltyReward = self.env["loyalty.reward"]
        LoyaltyCard = self.env["loyalty.card"]
        LoyaltyRule = self.env["loyalty.rule"]

        # Partner
        self.partner1 = self.env["res.partner"].create({"name": "Customer"})
        # Product Template
        self.membership_general = self.env["product.template"].create(
            {
                "name": "Membership (General) T",
                "list_price": 10,
            }
        )
        # Product Attributes
        (self.type_attribute, self.other_attribute) = self.env[
            "product.attribute"
        ].create(
            [
                {
                    "name": "Membership Type",
                    "sequence": 1,
                    "value_ids": [
                        Command.create(
                            {
                                "name": "Single",
                                "sequence": 1,
                            }
                        ),
                        Command.create(
                            {
                                "name": "Dual",
                                "sequence": 2,
                            }
                        ),
                    ],
                },
                {
                    "name": "Other",
                    "sequence": 1,
                    "value_ids": [
                        Command.create(
                            {
                                "name": "Test",
                                "sequence": 1,
                            }
                        ),
                        Command.create(
                            {
                                "name": "Test 2",
                                "sequence": 2,
                            }
                        ),
                    ],
                },
            ]
        )
        self.type_attribute.create_variant = "no_variant"
        self.other_attribute.create_variant = "no_variant"

        self.single, self.dual = self.type_attribute.value_ids
        self.test, self.test2 = self.other_attribute.value_ids

        self.MEMBERSHIP_TYPE_PTAL_VALUES = {
            "product_tmpl_id": self.membership_general.id,
            "attribute_id": self.type_attribute.id,
            "value_ids": [Command.set([self.single.id, self.dual.id])],
        }
        self.OTHER_PTAL_VALUES = {
            "product_tmpl_id": self.membership_general.id,
            "attribute_id": self.other_attribute.id,
            "value_ids": [Command.set([self.test.id, self.test2.id])],
        }

        self._add_membership_attribute_lines()

        membership_type_single = self._get_product_template_attribute_value(self.single)
        other_test = self._get_product_template_attribute_value(self.test)

        self.variant_single = self.membership_general._get_variant_for_combination(
            membership_type_single
        )
        self.variant_test = self.membership_general._get_variant_for_combination(
            other_test
        )

        self.loyalty_program = LoyaltyProgram.create(
            {
                "name": "Black Friday Sale",
                "program_type": "promotion",
                "trigger": "auto",
            }
        )
        self.loyalty_reward = LoyaltyReward.create(
            {
                "program_id": self.loyalty_program.id,
                "reward_type": "discount",
                "discount_mode": "percent",
                "discount": 10,
                "discount_product_ids": self.membership_general.product_variant_id,
                "discount_applicability": "specific",
            }
        )
        self.loyalty_card = LoyaltyCard.create({"program_id": self.loyalty_program.id})
        self.loyalty_rule = LoyaltyRule.create(
            {
                "program_id": self.loyalty_program.id,
                "minimum_amount": 10,
                "product_ids": self.membership_general.product_variant_id,
                "reward_point_amount": 10,
            }
        )

        self.so1 = self.env["sale.order"].create({"partner_id": self.partner1.id})
        self.so1.order_line = [
            Command.create(
                {
                    "product_id": self.variant_single.id,
                    "product_no_variant_attribute_value_ids": [
                        Command.link(membership_type_single.id)
                    ],
                }
            ),
            Command.create(
                {
                    "product_id": self.variant_test.id,
                    "product_no_variant_attribute_value_ids": [
                        Command.link(other_test.id)
                    ],
                }
            ),
        ]

    def _add_membership_attribute_lines(self):

        self._add_type_attribute_line()
        self._add_other_attribute_line()

    def _add_type_attribute_line(self):
        self.membership_type_attribute_lines = self.env[
            "product.template.attribute.line"
        ].create(self.MEMBERSHIP_TYPE_PTAL_VALUES)

        self._setup_type_attribute_line()

    def _setup_type_attribute_line(self):
        """Setup extra prices"""

        self.membership_type_attribute_lines.product_template_value_ids[
            0
        ].price_extra = 20
        self.membership_type_attribute_lines.product_template_value_ids[
            1
        ].price_extra = 35

    def _add_other_attribute_line(self):
        self.other_attribute_lines = self.env["product.template.attribute.line"].create(
            self.OTHER_PTAL_VALUES
        )

        self._setup_other_attribute_line()

    def _setup_other_attribute_line(self):
        """Setup extra prices"""

        self.other_attribute_lines.product_template_value_ids[0].price_extra = 15
        self.other_attribute_lines.product_template_value_ids[1].price_extra = 30

    def _get_product_value_id(
        self, product_template_attribute_lines, product_attribute_value
    ):
        return product_template_attribute_lines.product_template_value_ids.filtered(
            lambda product_value_id: product_value_id.product_attribute_value_id
            == product_attribute_value
        )[0]

    def _get_product_template_attribute_value(
        self, product_attribute_value, model=False
    ):
        """
        Return the `product.template.attribute.value` matching
            `product_attribute_value` for self.

        :param: recordset of one product.attribute.value
        :return: recordset of one product.template.attribute.value if found
            else empty
        """
        if not model:
            model = self.membership_general
        return model.valid_product_template_attribute_line_ids.filtered(
            lambda l: l.attribute_id == product_attribute_value.attribute_id
        ).product_template_value_ids.filtered(
            lambda v: v.product_attribute_value_id == product_attribute_value
        )

    def test_01_limit_discounted_attributes_disabled(self):
        """When adding promotions to a sales order total value should be updated accordingly"""
        self.assertEqual(
            self.so1.amount_total, 55, "Expected total without promotions to be 55"
        )
        self.so1.action_open_reward_wizard()

        # total after promotions should be 49.5:
        # 10*2 (list_price * nr of lines) + 20 (single attribute price)
        # + 15 (test attribute price) - (20+20+15)*0.1 (discount)
        self.assertEqual(
            self.so1.amount_total, 49.5, "Expected total with promotions to be 49.5"
        )

    def test_02_limit_discounted_attributes_attributes(self):
        """When adding promotions to a sales order total value should be updated accordingly
        In this case, it will be applied only to membership type attribute
        """

        self.loyalty_reward.limit_discounted_attributes = "attributes"
        self.loyalty_reward.discount_attribute_ids = self.type_attribute

        self.assertEqual(
            self.so1.amount_total, 55, "Expected total without promotions to be 55"
        )
        self.so1.action_open_reward_wizard()

        # total after promotions should be 53:
        # 10*2 (list_price * nr of lines) + 20 (single attribute price)
        # + 15 (test attribute price) - 20*0.1 (discount only on membership type attribute)
        self.assertEqual(
            self.so1.amount_total, 53, "Expected total with promotions to be 53"
        )

    def test_03_limit_discounted_attributes_list_price_attributes(self):
        """When adding promotions to a sales order total value should be updated accordingly
        In this case, it will be applied to both attributes and list_price
        """

        self.loyalty_reward.limit_discounted_attributes = "list_price"
        self.loyalty_reward.discount_attribute_ids = self.type_attribute
        self.assertEqual(
            self.so1.amount_total, 55, "Expected total without promotions to be 55"
        )
        self.so1.action_open_reward_wizard()

        # total after promotions should be 51:
        # 10*2 (list_price * nr of lines) + 20 (single attribute price)
        # + 15 (test attribute price) - (20+20)*0.1 (discount only on membership type attribute)
        self.assertEqual(
            self.so1.amount_total, 51, "Expected total with promotions to be 51"
        )
