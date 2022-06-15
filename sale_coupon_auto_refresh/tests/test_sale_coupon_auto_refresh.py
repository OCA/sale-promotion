# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common


class TestWebsiteSaleCouponAutorefresh(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        coupon_program_form = Form(
            cls.env["coupon.program"],
            view="sale_coupon.sale_coupon_program_view_promo_program_form",
        )
        coupon_program_form.name = "Test Discount Program"
        coupon_program_form.promo_code_usage = "no_code_needed"
        coupon_program_form.discount_type = "percentage"
        coupon_program_form.discount_percentage = 50
        coupon_program_form.discount_apply_on = "on_order"
        coupon_program_form.rule_minimum_amount = 100
        cls.coupon_program = coupon_program_form.save()
        cls.coupon_program.company_id.auto_refresh_coupon = True
        # Let's configure an extra trigger
        cls.env["ir.config_parameter"].set_param(
            "sale_coupon_auto_refresh.sale_order_triggers", "note"
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
