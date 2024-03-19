# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common


class TestWebsiteSaleCouponAutorefresh(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["loyalty.program"].search([]).write({"active": False})
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test pricelist",
                "item_ids": [
                    (
                        0,
                        0,
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
        cls.product = cls.env["product.product"].create({"name": "Test"})
        loyalty_program_form = Form(
            cls.env["loyalty.program"],
            view="sale_loyalty.loyalty_program_view_form_inherit_sale_loyalty",
        )
        loyalty_program_form.name = "Test Discount Program"
        loyalty_program_form.program_type = "promotion"
        cls.loyalty_program = loyalty_program_form.save()
        cls.loyalty_program.applies_on = "current"
        cls.loyalty_program.trigger = "auto"
        reward = cls.loyalty_program.reward_ids
        reward.reward_type = "discount"
        reward.discount = 50
        reward.discount_mode = "percent"
        reward.discount_applicability = "order"
        cls.loyalty_program.rule_ids.minimum_amount = 100
        cls.loyalty_program.company_id.auto_refresh_coupon = True
        # Let's configure an extra trigger
        cls.env["ir.config_parameter"].set_param(
            "sale_loyalty_auto_refresh.sale_order_triggers", "note"
        )

    def test_01_sale_coupon_auto_refresh_on_create(self):
        """Checks reward line proper creation after product line is added"""
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner

        # Create a product line that will trigger a reward line creation
        # (minimum amount >= 100 => create a reward line)
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1
            line_form.price_unit = 150
        sale = sale_form.save()
        discount_line = sale.order_line.filtered("is_reward_line")
        self.assertAlmostEqual(-75, discount_line.price_unit)

    def test_02_sale_coupon_auto_refresh_on_update(self):
        """Checks reward line proper update after product line is modified"""
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner

        # Create a product line that will NOT trigger a reward line creation
        # (minimum amount < 100 => do not create a reward line)
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1
            line_form.price_unit = 1
        sale = sale_form.save()
        discount_line = sale.order_line.filtered("is_reward_line")
        self.assertFalse(bool(discount_line))

        # Update product line in order to trigger reward line creation
        # (minimum amount >= 100 => create a reward line)
        sale_form = Form(sale.with_context(skip_auto_refresh_coupons=False))
        with sale_form.order_line.edit(index=0) as line_form:
            line_form.product_uom_qty = 10
            line_form.price_unit = 20
        sale_form.save()
        discount_line = sale.order_line.filtered("is_reward_line")
        self.assertEqual(1, len(discount_line))
        self.assertAlmostEqual(-100, discount_line.price_unit)

        # Create another product line that will trigger a reward line update
        # (total amount has changed => reward line price unit must change)
        sale_form = Form(sale.with_context(skip_auto_refresh_coupons=False))
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1
            line_form.price_unit = 40
        sale_form.save()
        discount_line = sale.order_line.filtered("is_reward_line")
        self.assertEqual(1, len(discount_line))
        self.assertAlmostEqual(-120, discount_line.price_unit)

        # Update product lines in order to delete reward line
        # (minimum amount < 100 => delete reward line)
        sale_form = Form(sale.with_context(skip_auto_refresh_coupons=False))
        with sale_form.order_line.edit(index=0) as line_form:
            line_form.product_uom_qty = 1
            line_form.price_unit = 1
        with sale_form.order_line.edit(index=2) as line_form:
            line_form.product_uom_qty = 1
            line_form.price_unit = 1
        sale_form.save()
        discount_line = sale.order_line.filtered("is_reward_line")
        self.assertFalse(bool(discount_line))

    def test_03_sale_coupon_auto_refresh_on_delete(self):
        """Checks reward line proper deletion after product line is deleted"""
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner

        # Create a product line that will trigger a reward line creation
        # (minimum amount >= 100 => create a reward line)
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1
            line_form.price_unit = 1000
        sale = sale_form.save()
        discount_line = sale.order_line.filtered("is_reward_line")
        self.assertEqual(1, len(discount_line))

        # Delete the product line that triggered the reward line creation
        # (minimum amount < 100 => delete reward line)
        sale_form = Form(sale.with_context(skip_auto_refresh_coupons=False))
        sale_form.order_line.remove(index=0)
        sale = sale_form.save()
        discount_line = sale.order_line.filtered("is_reward_line")
        self.assertFalse(bool(discount_line))

    def test_04_sale_coupon_auto_refresh_custom_triggers(self):
        """Checks reward line proper update after product line is modified"""
        self.env.company.auto_refresh_coupon = False
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        # Create a product line that would trigger the reward but we disabled it by
        # context
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 10
            line_form.price_unit = 20
        sale = sale_form.save()
        discount_line = sale.order_line.filtered("is_reward_line")
        self.assertFalse(bool(discount_line))
        self.env.company.auto_refresh_coupon = True
        sale.with_context(skip_auto_refresh_coupons=False).note = "Refresh!"
        # The promotions recompute is triggered an thus we get our reward
        discount_line = sale.order_line.filtered("is_reward_line")
        self.assertEqual(1, len(discount_line), "There should be a reward line")
        self.assertAlmostEqual(-100, discount_line.price_unit)

    def test_05_multi_programs(self):
        promo_60 = self.loyalty_program.copy(
            {
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "discount",
                            "discount": 60,
                            "discount_mode": "percent",
                            "discount_applicability": "order",
                        },
                    )
                ]
            }
        )
        reward_product = self.env["product.product"].create({"name": "Reward Product"})
        promo_prod = self.loyalty_program.copy(
            {
                "reward_ids": [
                    (
                        0,
                        0,
                        {
                            "reward_type": "product",
                            "reward_product_id": reward_product.id,
                            "reward_product_qty": 1,
                            "required_points": 1,
                        },
                    )
                ]
            }
        )
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        # Create a product line that would trigger the reward but we disabled it by
        # context
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 10
            line_form.price_unit = 20
        sale = sale_form.save()
        self.assertTrue(sale.coupon_point_ids)
        line_loyalty_program = sale.order_line.filtered(
            lambda line: line.reward_id == self.loyalty_program.reward_ids
        )
        line_promo_60 = sale.order_line.filtered(
            lambda line: line.reward_id == promo_60.reward_ids
        )
        line_promo_prod = sale.order_line.filtered(
            lambda line: line.reward_id == promo_prod.reward_ids
        )
        self.assertFalse(
            line_loyalty_program
        )  # Promo 60% is better, no select promo 50%
        self.assertTrue(line_promo_60)
        self.assertTrue(line_promo_prod)
