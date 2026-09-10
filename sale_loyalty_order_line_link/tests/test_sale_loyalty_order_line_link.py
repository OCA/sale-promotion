# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.tests import Form, tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestSaleCouponCriteriaMultiProduct(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_obj = cls.env["product.product"]
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test pricelist",
                "item_ids": [
                    Command.create(
                        {
                            "applied_on": "3_global",
                            "compute_price": "formula",
                            "base": "list_price",
                        },
                    )
                ],
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Mr. Odoo", "property_product_pricelist": cls.pricelist.id}
        )
        cls.product_a = product_obj.create({"name": "Product A", "list_price": 50})
        cls.product_b = product_obj.create({"name": "Product B", "list_price": 10})
        cls.product_c = product_obj.create({"name": "Product C", "list_price": 70})
        cls.tax_group = cls.env["account.tax.group"].create({"name": "Test Tax Group"})
        cls.tax_1 = cls.env["account.tax"].create(
            {
                "name": "Tax 10",
                "type_tax_use": "sale",
                "amount": 10,
                "tax_group_id": cls.tax_group.id,
                "country_id": cls.env.company.country_id.id,
            }
        )
        cls.tax_2 = cls.env["account.tax"].create(
            {
                "name": "Tax 4",
                "type_tax_use": "sale",
                "amount": 4,
                "tax_group_id": cls.tax_group.id,
                "country_id": cls.env.company.country_id.id,
            }
        )
        cls.loyalty_program = cls.env["loyalty.program"].create(
            {
                "name": "Test Coupon Line Link Program",
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
                            "discount_applicability": "specific",
                            "discount_product_ids": cls.product_a | cls.product_c,
                        },
                    )
                ],
            }
        )
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_a
            line_form.product_uom_qty = 1
            line_form.tax_ids.clear()
            line_form.tax_ids.add(cls.tax_1)
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_b
            line_form.product_uom_qty = 1
            line_form.tax_ids.clear()
            line_form.tax_ids.add(cls.tax_1)
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product_c
            line_form.product_uom_qty = 1
            line_form.tax_ids.clear()
            line_form.tax_ids.add(cls.tax_2)
        cls.sale = sale_form.save()
        cls.sale._update_programs_and_rewards()
        cls.wizard = (
            cls.env["sale.loyalty.reward.wizard"]
            .with_context(active_id=cls.sale)
            .create({"selected_reward_id": cls.loyalty_program.reward_ids.id})
        )

    def test_01_coupon_order_line_link_discount(self):
        """The reward lines always get the coupon program that applied it. For the order
        lines, three main cases are covered:
        - Discount on specific products. Only those lines get link to the reward lines.
        - Global discount. All the order lines get the link to the reward lines.
        """
        self.wizard.action_apply()
        lines = self.sale.order_line
        discount_line_1 = lines.filtered(
            lambda x: x.is_reward_line and self.tax_1 in x.tax_ids
        )
        discount_line_2 = lines.filtered(
            lambda x: x.is_reward_line and self.tax_2 in x.tax_ids
        )
        line_a = lines.filtered(lambda x: x.product_id == self.product_a)
        line_b = lines.filtered(lambda x: x.product_id == self.product_b)
        line_c = lines.filtered(lambda x: x.product_id == self.product_c)
        # Two discount are created from the program
        self.assertEqual(discount_line_1.reward_id, self.loyalty_program.reward_ids)
        self.assertEqual(discount_line_2.reward_id, self.loyalty_program.reward_ids)
        # Only the program specific products get the link to the reward lines
        self.assertEqual(line_a.reward_line_ids, discount_line_1)
        self.assertFalse(line_b.reward_line_ids)
        self.assertEqual(line_c.reward_line_ids, discount_line_2)
        # All the lines apply on the domain
        self.assertEqual(
            line_a.reward_generated_line_ids, discount_line_1 | discount_line_2
        )
        self.assertEqual(
            line_b.reward_generated_line_ids, discount_line_1 | discount_line_2
        )
        self.assertEqual(
            line_c.reward_generated_line_ids, discount_line_1 | discount_line_2
        )
        # Change the program discount type to a global discount. Now all the lines
        # have a link to the coupon reward lines
        self.loyalty_program.reward_ids.discount_applicability = "order"
        self.sale._update_programs_and_rewards()
        self.assertEqual(line_a.reward_line_ids, discount_line_1)
        self.assertEqual(line_b.reward_line_ids, discount_line_1)
        self.assertEqual(line_c.reward_line_ids, discount_line_2)

    def test_02_coupon_order_line_link_discount_cheapest(self):
        """Change the program discount type to a cheapest product. Now only the chepest
        line will get the reward."""
        self.loyalty_program.reward_ids.write(
            {
                "discount_applicability": "cheapest",
                "discount_product_ids": [Command.link(self.product_b.id)],
            }
        )
        self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_b
        ).product_uom_qty = 1
        self.wizard.action_apply()
        lines = self.sale.order_line
        discount_line_1 = lines.filtered(
            lambda x: x.is_reward_line and self.tax_1 in x.tax_ids
        )
        discount_line_2 = lines.filtered(
            lambda x: x.is_reward_line and self.tax_2 in x.tax_ids
        )
        line_a = lines.filtered(lambda x: x.product_id == self.product_a)
        line_b = lines.filtered(lambda x: x.product_id == self.product_b)
        line_c = lines.filtered(lambda x: x.product_id == self.product_c)
        self.assertEqual(discount_line_1.reward_id, self.loyalty_program.reward_ids)
        self.assertEqual(line_b.reward_line_ids, discount_line_1)
        self.assertFalse(line_a.reward_line_ids)
        self.assertFalse(line_c.reward_line_ids)
        discount_line_2 = self.sale.order_line.filtered(
            lambda x: x.is_reward_line and self.tax_2 in x.tax_ids
        )
        self.assertFalse(discount_line_2, "There shouldn't be a reward for tax 2")

    def test_03_coupon_order_line_link_product(self):
        """The reward lines are linked to the coupon programs and the lines that
        genereate the reward line are linked to that
        """
        # Let's set up the program for product rewards
        self.loyalty_program.rule_ids.write(
            {"product_domain": '[["product_variant_ids.name","=","Product A"]]'}
        )
        self.loyalty_program.reward_ids.write(
            {
                "reward_type": "product",
                "reward_product_id": self.product_c,
                "reward_product_qty": 5,
            }
        )
        self.wizard.action_apply()
        lines = self.sale.order_line
        reward_line = self.sale.order_line.filtered(lambda x: x.is_reward_line)
        line_a = lines.filtered(lambda x: x.product_id == self.product_a)
        line_b = lines.filtered(lambda x: x.product_id == self.product_b)
        line_c = lines.filtered(lambda x: x.product_id == self.product_c)
        self.assertEqual(reward_line.reward_id.program_id, self.loyalty_program)
        self.assertFalse(line_a.reward_line_ids)
        self.assertFalse(line_b.reward_line_ids)
        self.assertTrue(line_a.reward_generated_line_ids)
        self.assertEqual(line_c.reward_origin_generated_line_ids, line_a)
        self.assertTrue(line_c.reward_line_ids)
        self.assertEqual(line_a.reward_generated_line_ids, reward_line)
        self.assertFalse(line_b.reward_generated_line_ids)

    def test_04_select_additional_fields(self):
        # Call the _select_additional_fields method
        sale_report = self.env["sale.report"]
        fields = sale_report._select_additional_fields()

        # Assert that the loyalty_program_id field is included
        self.assertIn(
            "clr.program_id",
            fields.values(),
            "The 'loyalty_program_id' field is not added to the select statement.",
        )

    def test_05_group_by_sale(self):
        # Call the _group_by_sale method
        sale_report = self.env["sale.report"]
        group_by_fields = sale_report._group_by_sale()

        # Assert that 'clr.program_id' is included in the GROUP BY clause
        self.assertIn(
            "clr.program_id",
            group_by_fields,
            "The 'loyalty_program_id' field is not included in the GROUP BY clause.",
        )
