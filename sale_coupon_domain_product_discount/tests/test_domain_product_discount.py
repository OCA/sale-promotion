# Copyright 2022 Ooops404
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged
from odoo.tests.common import SavepointCase


@tagged("post_install", "-at_install")
class CetmixTestSaleCouponProgram(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        product_obj = cls.env["product.product"]
        cls.largeCabinet = product_obj.create(
            {
                "name": "Large Cabinet",
                "list_price": 50.0,
                "taxes_id": False,
            }
        )
        cls.conferenceChair = product_obj.create(
            {
                "name": "Conference Chair",
                "list_price": 100,
                "taxes_id": False,
            }
        )
        cls.pedalBin = product_obj.create(
            {
                "name": "Pedal Bin",
                "list_price": 150,
                "taxes_id": False,
            }
        )
        cls.drawerBlack = product_obj.create(
            {
                "name": "Drawer Black",
                "list_price": 200,
                "taxes_id": False,
            }
        )
        cls.steve = cls.env["res.partner"].create(
            {
                "name": "Steve Bucknor",
                "email": "steve.bucknor@example.com",
            }
        )
        cls.order = cls.env["sale.order"].create({"partner_id": cls.steve.id})
        # Add products in order
        cls.large_cabinet_line = cls.env["sale.order.line"].create(
            {
                "product_id": cls.largeCabinet.id,
                "name": "Large Cabinet",
                "product_uom_qty": 7.0,
                "order_id": cls.order.id,
            }
        )
        cls.sale_order_line_obj = cls.env["sale.order.line"]
        cls.conference_chair_line = cls.sale_order_line_obj.create(
            {
                "product_id": cls.conferenceChair.id,
                "name": "Conference Chair",
                "product_uom_qty": 5.0,
                "order_id": cls.order.id,
            }
        )
        cls.pedal_bin_line = cls.sale_order_line_obj.create(
            {
                "product_id": cls.pedalBin.id,
                "name": "Pedal Bin",
                "product_uom_qty": 10.0,
                "order_id": cls.order.id,
            }
        )
        cls.drawer_black_line = cls.sale_order_line_obj.create(
            {
                "product_id": cls.drawerBlack.id,
                "name": "Drawer Black",
                "product_uom_qty": 2.0,
                "order_id": cls.order.id,
            }
        )

    def test_program_reward_discount_domain_matching(self):
        """
        Test program with reward type is `discount` for domain matching of product
        """
        # Now we want to apply a 10% discount only on Large Cabinet and Pedal Bin
        program = self.env["coupon.program"].create(
            {
                "name": "10% reduction on Large Cabinet and Pedal Bin in cart",
                "promo_code_usage": "no_code_needed",
                "reward_type": "discount",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 10.0,
                "rule_products_domain": "[('id', 'in', [%s, %s])]"
                % (self.largeCabinet.id, self.pedalBin.id),
                "active": True,
                "discount_apply_on": "domain_product",
            }
        )

        self.assertEqual(
            len(self.order.order_line.ids), 4, "We should not get the reduction line"
        )

        # amount total of the
        # order = sum([line.price_unit*line.product_uom_qty for line in self.order.order_line])
        self.assertEqual(
            self.order.amount_total,
            2750.0,
            "The order total with programs should be 2750.00",
        )

        # Apply all the programs
        self.order.recompute_coupon_lines()
        self.assertEqual(
            len(self.order.order_line.ids),
            5,
            "We should now get the reduction line",
        )

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

    def test_program_reward_discount_domain_matching_with_tax_and_rule(self):
        """
        Test program with reward type is `discount` for domain matching of product with taxes
        """
        percent_tax = self.env["account.tax"].create(
            {
                "name": "15% Tax",
                "amount_type": "percent",
                "amount": 15,
                "price_include": True,
            }
        )
        self.env["coupon.program"].create(
            {
                "name": "10% reduction on Large Cabinet and Pedal Bin in cart",
                "promo_code_usage": "no_code_needed",
                "reward_type": "discount",
                "program_type": "promotion_program",
                "discount_type": "percentage",
                "discount_percentage": 10.0,
                "rule_products_domain": "[('id', 'in', [%s, %s])]"
                % (self.largeCabinet.id, self.pedalBin.id),
                "active": True,
                "discount_apply_on": "domain_product",
                "rule_minimum_amount": 2800.00,
                "rule_minimum_amount_tax_inclusion": "tax_included",
            }
        )
        self.largeCabinet.taxes_id = percent_tax
        self.pedalBin.taxes_id = percent_tax
        self.large_cabinet_line.tax_id = [(6, 0, percent_tax.ids)]
        self.pedal_bin_line.tax_id = [(6, 0, percent_tax.ids)]
        self.order.recompute_coupon_lines()
        self.assertEqual(
            len(self.order.order_line),
            4,
            "We should not get the reduction line total amount of the order 2750.0",
        )
        self.large_cabinet_line.tax_id.price_include = False
        self.pedal_bin_line.tax_id.price_include = False
        self.large_cabinet_line._compute_tax_id()
        self.pedal_bin_line._compute_tax_id()
        self.order.recompute_coupon_lines()
        self.assertEqual(
            len(self.order.order_line),
            5,
            "We should now get the reduction line since we have more than 2800.0",
        )
