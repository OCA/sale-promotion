# Copyright 2022 Ooops404
# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, tagged

from odoo.addons.coupon_domain_product_discount.tests.test_domain_product_discount import (
    CouponDomainProductDiscount,
)


@tagged("post_install", "-at_install")
class TestSaleCouponDomainProductDiscount(CouponDomainProductDiscount):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Let's prepare a sale order to play with
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.steve
        sale_form.pricelist_id = cls.pricelist
        with sale_form.order_line.new() as line:
            line.product_id = cls.largeCabinet
            line.product_uom_qty = 7
        with sale_form.order_line.new() as line:
            line.product_id = cls.conferenceChair
            line.product_uom_qty = 5
        with sale_form.order_line.new() as line:
            line.product_id = cls.pedalBin
            line.product_uom_qty = 10
        with sale_form.order_line.new() as line:
            line.product_id = cls.drawerBlack
            line.product_uom_qty = 2
        cls.order = sale_form.save()

    def _create_promo(self):
        """Common promo case for tests"""
        program_form = Form(
            self.env["coupon.program"],
            view="coupon.coupon_program_view_promo_program_form",
        )
        program_form.name = "10% reduction on Large Cabinet and Pedal Bin in cart"
        program_form.promo_code_usage = "no_code_needed"
        program_form.reward_type = "discount"
        program_form.discount_type = "percentage"
        program_form.discount_percentage = 10.0
        program_form.rule_products_domain = "[('id', 'in', [%s, %s])]" % (
            self.largeCabinet.id,
            self.pedalBin.id,
        )
        program_form.discount_apply_on = "specific_products"
        program_form.discount_apply_on_domain_product = True
        return program_form

    def test_program_reward_discount_domain_matching(self):
        """
        Test program with reward type is `discount` for domain matching of product
        """
        # Now we want to apply a 10% discount only on Large Cabinet and Pedal Bin
        program_form = self._create_promo()
        program = program_form.save()
        self.assertFalse(
            self.order.order_line.filtered("is_reward_line"),
            "We should not get the reduction line",
        )
        # Amount total of the
        # order = sum([line.price_unit*line.product_uom_qty for line in self.order.order_line])
        self.assertEqual(
            self.order.amount_total,
            2750.0,
            "The order total with programs should be 2750.00",
        )
        # Apply all the programs
        self.order.recompute_coupon_lines()
        line = self.order.order_line.filtered("is_reward_line")
        self.assertTrue(bool(line), "We should now get the reduction line")
        # Check amount total after apply coupon: 2750-(50*7+150*10)*0.1
        self.assertEqual(
            self.order.amount_total,
            2565.0,
            "The order total with programs should be 2565.00",
        )
        program.discount_max_amount = 100
        self.order.recompute_coupon_lines()
        self.assertEqual(
            self.order.amount_total,
            2650.0,
            "The order total with programs should be 2650.00",
        )
        # Stric limit
        program.strict_per_product_limit = True
        # Only the Pedal Bin will be discounted
        program.rule_min_quantity = 10
        program.discount_max_amount = 0
        self.order.recompute_coupon_lines()
        self.assertAlmostEqual(
            self.order.amount_total,
            2600.0,
            "Only the Pedal Bin will be discounted (2750 - 150)",
        )
        program.rule_min_quantity = 11
        self.order.recompute_coupon_lines()
        self.assertFalse(
            self.order.order_line.filtered("is_reward_line"),
            "The promotion should be gone as we raise the condition",
        )

    def test_program_reward_discount_domain_matching_with_tax_and_rule(self):
        """
        Test program with reward type is `discount` for domain matching of product with taxes
        """
        program_form = self._create_promo()
        program_form.rule_minimum_amount = 2800
        program_form.rule_minimum_amount_tax_inclusion = "tax_included"
        program_form.save()
        # Setup product taxes
        self.largeCabinet.taxes_id = self.percent_tax
        self.pedalBin.taxes_id = self.percent_tax
        for line in self.order.order_line:
            line.tax_id = [(6, 0, self.percent_tax.ids)]
        self.order.recompute_coupon_lines()
        self.assertFalse(
            self.order.order_line.filtered("is_reward_line"),
            "We should not get the reduction line total amount of the order 2750.0",
        )
        self.percent_tax.price_include = False
        for line in self.order.order_line:
            line._compute_tax_id()
        self.order.recompute_coupon_lines()
        line = self.order.order_line.filtered("is_reward_line")
        self.assertTrue(
            bool(line),
            "We should now get the reduction line since we have more than 2800.0",
        )
