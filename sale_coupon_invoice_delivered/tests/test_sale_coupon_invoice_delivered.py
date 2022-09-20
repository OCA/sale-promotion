from odoo.tests import Form, tagged

from .common import TestSaleCouponInvoiceDeliveredCommon


@tagged("post_install", "-at_install")
class TestSaleCouponInvoiceDelivered(TestSaleCouponInvoiceDeliveredCommon):
    def test_sale_coupon_invoice_delivered_without_invoice_on_delivered_option(self):
        order = self.empty_order
        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Discounted Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
                "discount": 50.0,
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": self.conferenceChair.id,
                "name": "Conference chair",
                "product_uom_qty": 4.0,
                "order_id": order.id,
            }
        )

        self.global_promo.invoice_on_delivered = False

        self.assertEqual(
            order.amount_total,
            226.0,  # 320/2 + 4 * 16.5
            "Before computing promotions, total should be the sum of product price.",
        )

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            203.4,  # 226 - 0.1 * 226
            2,
            "The global discount is applied",
        )

        self.assertEqual("Discounted Large Cabinet", order.order_line[0].name)
        self.assertEqual(
            order.order_line[0].qty_delivered, 0, "There is no quantity delivered"
        )
        self.assertIn("Conference chair", order.order_line[1].name)
        self.assertEqual(
            order.order_line[1].qty_delivered, 0, "There is no quantity delivered"
        )
        self.assertIn("Discount: 10%", order.order_line[2].name)
        self.assertEqual(order.order_line[2].product_uom_qty, 1)
        self.assertEqual(
            order.order_line[2].qty_delivered, 0, "There is no quantity delivered"
        )

    def test_sale_coupon_invoice_delivered_full_delivery(self):
        order = self.empty_order
        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Discounted Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
                "discount": 50.0,
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": self.conferenceChair.id,
                "name": "Conference chair",
                "product_uom_qty": 4.0,
                "order_id": order.id,
            }
        )

        self.assertEqual(
            order.amount_total,
            226.0,  # 320/2 + 4 * 16.5
            "Before computing promotions, total should be the sum of product price.",
        )

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            203.4,  # 226 - 0.1 * 226
            2,
            "The global discount is applied",
        )

        self.assertEqual("Discounted Large Cabinet", order.order_line[0].name)
        self.assertEqual(
            order.order_line[0].qty_delivered, 0, "There is no quantity delivered"
        )
        self.assertIn("Conference chair", order.order_line[1].name)
        self.assertEqual(
            order.order_line[1].qty_delivered, 0, "There is no quantity delivered"
        )
        self.assertIn("Discount: 10%", order.order_line[2].name)
        self.assertEqual(
            order.order_line[2].qty_delivered, 0, "There is no quantity delivered"
        )

        order.action_confirm()
        order.picking_ids.move_line_ids[0].qty_done = 1
        order.picking_ids.move_line_ids[1].qty_done = 4

        picking = order.picking_ids.ensure_one()
        self.assertEqual(picking.button_validate(), True)

        self.assertEqual("Discounted Large Cabinet", order.order_line[0].name)
        self.assertEqual(
            order.order_line[0].qty_delivered, 1, "Product has been delivered"
        )
        self.assertIn("Conference chair", order.order_line[1].name)
        self.assertEqual(
            order.order_line[1].qty_delivered, 4, "Product has been delivered"
        )
        self.assertIn("Discount: 10%", order.order_line[2].name)
        self.assertEqual(
            order.order_line[2].qty_delivered, 1, "Promo is considered fully delivered"
        )

    def test_sale_coupon_invoice_delivered_partial_delivery(self):
        order = self.empty_order
        self.env["sale.order.line"].create(
            {
                "product_id": self.largeCabinet.id,
                "name": "Discounted Large Cabinet",
                "product_uom_qty": 1.0,
                "order_id": order.id,
                "discount": 50.0,
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": self.conferenceChair.id,
                "name": "Conference chair",
                "product_uom_qty": 4.0,
                "order_id": order.id,
            }
        )

        self.assertEqual(
            order.amount_total,
            226.0,  # 320/2 + 4 * 16.5
            "Before computing promotions, total should be the sum of product price.",
        )

        order.recompute_coupon_lines()

        self.assertAlmostEqual(
            order.amount_total,
            203.4,  # 226 - 0.1 * 226
            2,
            "The global discount is applied",
        )

        self.assertEqual("Discounted Large Cabinet", order.order_line[0].name)
        self.assertEqual(
            order.order_line[0].qty_delivered, 0, "There is no quantity delivered"
        )
        self.assertIn("Conference chair", order.order_line[1].name)
        self.assertEqual(
            order.order_line[1].qty_delivered, 0, "There is no quantity delivered"
        )
        self.assertIn("Discount: 10%", order.order_line[2].name)
        self.assertEqual(
            order.order_line[2].qty_delivered, 0, "There is no quantity delivered"
        )

        order.action_confirm()
        order.picking_ids.move_line_ids[0].qty_done = 1
        order.picking_ids.move_line_ids[1].qty_done = 2

        picking = order.picking_ids.ensure_one()
        res = picking.button_validate()
        # Create backorder
        Form(self.env[res["res_model"]].with_context(res["context"])).save().process()
        self.assertEqual(len(order.picking_ids), 2)

        self.assertEqual("Discounted Large Cabinet", order.order_line[0].name)
        self.assertEqual(
            order.order_line[0].qty_delivered, 1, "Product has been delivered"
        )
        self.assertIn("Conference chair", order.order_line[1].name)
        self.assertEqual(
            order.order_line[1].qty_delivered, 2, "Product has been partially delivered"
        )
        self.assertIn("Discount: 10%", order.order_line[2].name)
        self.assertAlmostEqual(
            order.order_line[2].qty_delivered,
            # Total reduction = 0.1 * 226 = 22.6
            # Delivered reduction 0.1 * (320/2 + 2 * 16.5) = 19.3
            0.85,  # 19.3 / 22.6 = 0.8539823008849557...
            2,
            "Promo is therefore partially delivered",
        )

        backorder = order.picking_ids.filtered(
            lambda p: p.state == "assigned"
        ).ensure_one()
        backorder.move_line_ids[0].qty_done = 1
        res = backorder.button_validate()
        # Create backorder
        Form(self.env[res["res_model"]].with_context(res["context"])).save().process()
        self.assertEqual(len(order.picking_ids), 3)

        self.assertEqual("Discounted Large Cabinet", order.order_line[0].name)
        self.assertEqual(
            order.order_line[0].qty_delivered, 1, "Product has been delivered"
        )
        self.assertIn("Conference chair", order.order_line[1].name)
        self.assertEqual(
            order.order_line[1].qty_delivered, 3, "Product has been partially delivered"
        )
        self.assertIn("Discount: 10%", order.order_line[2].name)
        self.assertAlmostEqual(
            order.order_line[2].qty_delivered,
            # Total reduction = 0.1 * 226 = 22.6
            # Delivered reduction 0.1 * (320/2 + 3 * 16.5) = 20.95
            0.93,  # 20.95 / 22.6  = 0.9269911504424778...
            2,
            "Promo is therefore partially delivered",
        )

        backorder = order.picking_ids.filtered(
            lambda p: p.state == "assigned"
        ).ensure_one()
        backorder.move_line_ids[0].qty_done = 1
        self.assertEqual(backorder.button_validate(), True)
        self.assertEqual(len(order.picking_ids), 3)

        self.assertEqual("Discounted Large Cabinet", order.order_line[0].name)
        self.assertEqual(
            order.order_line[0].qty_delivered, 1, "Product has been delivered"
        )
        self.assertIn("Conference chair", order.order_line[1].name)
        self.assertEqual(
            order.order_line[1].qty_delivered, 4, "Product has been delivered"
        )
        self.assertIn("Discount: 10%", order.order_line[2].name)
        self.assertEqual(
            order.order_line[2].qty_delivered, 1, "Promo is considered fully delivered"
        )
