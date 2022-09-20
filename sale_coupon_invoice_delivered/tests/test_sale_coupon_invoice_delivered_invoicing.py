from odoo.tests import Form, tagged

from .common import TestSaleCouponInvoiceDeliveredCommon


@tagged("post_install", "-at_install")
class TestSaleCouponInvoiceDeliveredInvoicing(TestSaleCouponInvoiceDeliveredCommon):
    def test_sale_coupon_invoice_delivered_invoicing_full_delivery(self):
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
        invoice = order._create_invoices(final=True).ensure_one()
        invoice.action_post()

        self.assertEqual("Discounted Large Cabinet", invoice.invoice_line_ids[0].name)
        self.assertEqual(
            invoice.invoice_line_ids[0].quantity, 1, "Product has been invoiced"
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_unit, 320, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_total, 160, 2)
        self.assertIn("Conference chair", invoice.invoice_line_ids[1].name)
        self.assertEqual(
            invoice.invoice_line_ids[1].quantity, 4, "Product has been invoiced"
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_unit, 16.5, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_total, 66.0, 2)
        self.assertIn("Discount: 10%", invoice.invoice_line_ids[2].name)
        self.assertEqual(
            invoice.invoice_line_ids[2].quantity, 1, "Discount has been fully invoiced"
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[2].price_unit, -22.6, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[2].price_total, -22.6, 2)

    def test_sale_coupon_invoice_delivered_invoicing_partial_delivery(self):
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
            order.order_line[2].qty_invoiced,
            0,
            2,
            "Promo is not invoiced",
        )
        self.assertAlmostEqual(
            order.order_line[2].qty_delivered,
            # Total reduction = 0.1 * 226 = 22.6
            # Delivered reduction 0.1 * (320/2 + 2 * 16.5) = 19.3
            0.85,  # 19.3 / 22.6 = 0.8539823008849557...
            2,
            "Promo is therefore partially delivered",
        )

        invoice = order._create_invoices(final=True).ensure_one()
        invoice.action_post()

        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            0.85,
            2,
            "Promo is now partially invoiced",
        )

        self.assertEqual("Discounted Large Cabinet", invoice.invoice_line_ids[0].name)
        self.assertEqual(
            invoice.invoice_line_ids[0].quantity, 1, "Product has been invoiced"
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_unit, 320, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_total, 160, 2)
        self.assertIn("Conference chair", invoice.invoice_line_ids[1].name)
        self.assertEqual(
            invoice.invoice_line_ids[1].quantity,
            2,
            "Product has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_unit, 16.5, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_total, 33.0, 2)
        self.assertIn("Discount: 10%", invoice.invoice_line_ids[2].name)
        self.assertEqual(
            invoice.invoice_line_ids[2].quantity,
            0.85,  # with full float should be 0.8539823008849557
            "Discount has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[2].price_unit, -22.6, 2)
        # FIXME: This is wrong:
        self.assertAlmostEqual(invoice.invoice_line_ids[2].price_total, -19.21, 2)
        # SHOULD be
        # self.assertAlmostEqual(invoice.invoice_line_ids[2].price_total, -19.3, 2)

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
            order.order_line[2].qty_invoiced,
            0.85,
            2,
            "Promo is partially invoiced",
        )
        self.assertAlmostEqual(
            order.order_line[2].qty_delivered,
            # Total reduction = 0.1 * 226 = 22.6
            # Delivered reduction 0.1 * (320/2 + 3 * 16.5) = 20.95
            0.93,  # 20.95 / 22.6 = 0.9269911504424778...
            2,
            "Promo is therefore partially delivered",
        )

        invoice = order._create_invoices(final=True).ensure_one()
        invoice.action_post()

        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            0.93,
            2,
            "Promo is more partially invoiced",
        )

        self.assertIn("Conference chair", invoice.invoice_line_ids[0].name)
        self.assertEqual(
            invoice.invoice_line_ids[0].quantity,
            1,
            "Product has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_unit, 16.5, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_total, 16.5, 2)
        self.assertIn("Discount: 10%", invoice.invoice_line_ids[1].name)
        self.assertEqual(
            invoice.invoice_line_ids[1].quantity,
            0.08,  # 0.93 - 0.85 = 0.08 (with full float should be 0.07300884955752207)
            "Discount has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_unit, -22.6, 2)
        # FIXME: This is wrong:
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_total, -1.81, 2)
        # SHOULD be
        # self.assertAlmostEqual(invoice.invoice_line_ids[1].price_total, -1.65, 2)

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

        invoice = order._create_invoices(final=True).ensure_one()

        invoice.action_post()
        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            1,
            2,
            "Promo is fully invoiced",
        )

        self.assertIn("Conference chair", invoice.invoice_line_ids[0].name)
        self.assertEqual(
            invoice.invoice_line_ids[0].quantity,
            1,
            "Product has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_unit, 16.5, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_total, 16.5, 2)
        self.assertIn("Discount: 10%", invoice.invoice_line_ids[1].name)
        self.assertEqual(
            invoice.invoice_line_ids[1].quantity,
            0.07,  # 1 - 0.93 = 0.07 (with full float should be 0.07300884955752207)
            "Discount has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_unit, -22.6, 2)
        # FIXME: This is also wrong:
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_total, -1.58, 2)
        # SHOULD be
        # self.assertAlmostEqual(invoice.invoice_line_ids[1].price_total, -1.65, 2)

        # All in all we get back on our feet due to invoice quantity computation
        # Total discount theory: -19.3 - 1.65 - 1.65 = -22.6
        # Total discount real: -19.21 - 1.81 - 1.58 = -22.6

    def test_sale_coupon_invoice_delivered_invoicing_partial_delivery_with_precise_uom(
        self,
    ):
        # Set Product UoM to 8 decimal places
        self.env["decimal.precision"].search(
            [("name", "=", "Product Unit of Measure")]
        ).write({"digits": 8})

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
            order.order_line[2].qty_invoiced,
            0,
            2,
            "Promo is not invoiced",
        )
        self.assertAlmostEqual(
            order.order_line[2].qty_delivered,
            # Total reduction = 0.1 * 226 = 22.6
            # Delivered reduction 0.1 * (320/2 + 2 * 16.5) = 19.3
            0.85398230,  # 19.3 / 22.6 = 0.8539823008849557...
            8,
            "Promo is therefore partially delivered",
        )

        invoice = order._create_invoices(final=True).ensure_one()
        invoice.action_post()

        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            0.85398230,
            8,
            "Promo is now partially invoiced",
        )

        self.assertEqual("Discounted Large Cabinet", invoice.invoice_line_ids[0].name)
        self.assertEqual(
            invoice.invoice_line_ids[0].quantity, 1, "Product has been invoiced"
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_unit, 320, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_total, 160, 2)
        self.assertIn("Conference chair", invoice.invoice_line_ids[1].name)
        self.assertEqual(
            invoice.invoice_line_ids[1].quantity,
            2,
            "Product has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_unit, 16.5, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_total, 33.0, 2)
        self.assertIn("Discount: 10%", invoice.invoice_line_ids[2].name)
        self.assertEqual(
            invoice.invoice_line_ids[2].quantity,
            0.85398230,  # with full float should be 0.8539823008849557
            "Discount has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[2].price_unit, -22.6, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[2].price_total, -19.3, 2)

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
            order.order_line[2].qty_invoiced,
            0.85398230,
            8,
            "Promo is partially invoiced",
        )
        self.assertAlmostEqual(
            order.order_line[2].qty_delivered,
            # Total reduction = 0.1 * 226 = 22.6
            # Delivered reduction 0.1 * (320/2 + 3 * 16.5) = 20.95
            0.92699115,  # 20.95 / 22.6 = 0.9269911504424778
            8,
            "Promo is therefore partially delivered",
        )

        invoice = order._create_invoices(final=True).ensure_one()
        invoice.action_post()

        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            0.92699115,
            8,
            "Promo is more partially invoiced",
        )

        self.assertIn("Conference chair", invoice.invoice_line_ids[0].name)
        self.assertEqual(
            invoice.invoice_line_ids[0].quantity,
            1,
            "Product has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_unit, 16.5, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_total, 16.5, 2)
        self.assertIn("Discount: 10%", invoice.invoice_line_ids[1].name)
        self.assertEqual(
            invoice.invoice_line_ids[1].quantity,
            0.07300885,  # 0.92699115 - 0.85398230 = 0.07300885
            # (with full float should be 0.07300884955752207)
            "Discount has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_unit, -22.6, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_total, -1.65, 2)

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

        invoice = order._create_invoices(final=True).ensure_one()

        invoice.action_post()
        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            1,
            2,
            "Promo is fully invoiced",
        )

        self.assertIn("Conference chair", invoice.invoice_line_ids[0].name)
        self.assertEqual(
            invoice.invoice_line_ids[0].quantity,
            1,
            "Product has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_unit, 16.5, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_total, 16.5, 2)
        self.assertIn("Discount: 10%", invoice.invoice_line_ids[1].name)
        self.assertEqual(
            invoice.invoice_line_ids[1].quantity,
            0.07300885,  # 1 - 0.92699115 = 0.07300885
            # (with full float should be 0.07300884955752207)
            "Discount has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_unit, -22.6, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_total, -1.65, 2)

    def test_sale_coupon_invoice_delivered_invoicing_partial_delivery_with_post_order_changes(
        self,
    ):
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
            order.order_line[2].price_total,
            -22.6,
            2,
        )
        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            0,
            2,
            "Promo is not invoiced",
        )
        self.assertAlmostEqual(
            order.order_line[2].qty_delivered,
            # Total reduction = 0.1 * 226 = 22.6
            # Delivered reduction 0.1 * (320/2 + 2 * 16.5) = 19.3
            0.85,  # 19.3 / 22.6 = 0.8539823008849557...
            2,
            "Promo is therefore partially delivered",
        )

        # No warning before invoicing
        self.assertFalse(
            order.order_line[0]._onchange_product_uom_qty().get("warning", False)
        )

        invoice = order._create_invoices(final=True).ensure_one()
        invoice.action_post()

        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            0.85,
            2,
            "Promo is now partially invoiced",
        )

        self.assertEqual("Discounted Large Cabinet", invoice.invoice_line_ids[0].name)
        self.assertEqual(
            invoice.invoice_line_ids[0].quantity, 1, "Product has been invoiced"
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_unit, 320, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_total, 160, 2)
        self.assertIn("Conference chair", invoice.invoice_line_ids[1].name)
        self.assertEqual(
            invoice.invoice_line_ids[1].quantity,
            2,
            "Product has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_unit, 16.5, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_total, 33.0, 2)
        self.assertIn("Discount: 10%", invoice.invoice_line_ids[2].name)
        self.assertEqual(
            invoice.invoice_line_ids[2].quantity,
            0.85,
            "Discount has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[2].price_unit, -22.6, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[2].price_total, -19.21, 2)

        # Now for the interesting part
        # Let's add 49 cabinets

        order.order_line[0].write({"product_uom_qty": 50})

        # This MUST trigger a warning in the UI
        self.assertEqual(
            order.order_line[0]._onchange_product_uom_qty()["warning"]["title"],
            "Ordered quantity changed on already invoiced order!",
        )
        order.recompute_coupon_lines()

        self.assertEqual("Discounted Large Cabinet", order.order_line[0].name)
        self.assertEqual(order.order_line[0].product_uom_qty, 50)
        self.assertEqual(
            order.order_line[0].qty_delivered, 1, "Product has only one unit delivered"
        )

        self.assertIn("Discount: 10%", order.order_line[2].name)
        # New promo price increase
        self.assertAlmostEqual(
            order.order_line[2].price_total,
            -806.6,
            2,
        )
        # Quantity delivered decrease
        self.assertAlmostEqual(
            order.order_line[2].qty_delivered,
            0.02,
            2,
            "Promo is therefore partially delivered",
        )

        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            0.85,  # FIXME: Here should probably be considered: 0.02
            2,
            "Promo is partially invoiced",
        )

        # Let's make a backorder to make a new invoice

        backorder = order.picking_ids.filtered(
            lambda p: p.state == "assigned"
        ).ensure_one()

        backorder.move_line_ids.filtered(
            lambda m: m.product_id.name == "Conference Chair"
        ).qty_done = 1
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
            order.order_line[2].qty_invoiced,
            0.85,
            2,
            "Promo is partially invoiced",
        )
        self.assertAlmostEqual(
            order.order_line[2].qty_delivered,
            0.03,
            2,
            "Promo is therefore partially delivered",
        )

        invoice = order._create_invoices(final=True).ensure_one()
        invoice.action_post()

        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            0.03,  # Invoiced quantity is now correct
            2,
        )

        self.assertIn("Conference chair", invoice.invoice_line_ids[0].name)
        self.assertEqual(
            invoice.invoice_line_ids[0].quantity,
            1,
            "Product has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_unit, 16.5, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_total, 16.5, 2)
        self.assertIn("Discount: 10%", invoice.invoice_line_ids[1].name)

        # Yeah that's bad
        self.assertAlmostEqual(
            invoice.invoice_line_ids[1].quantity,
            -0.82,
            2,
            "Discount has been negatively invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_unit, -806.6, 2)
        # Very bad, now customer has to pay 600$ for nothing
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_total, 661.41, 2)

    def test_sale_coupon_invoice_delivered_invoicing_partial_delivery_fixed_amount(
        self,
    ):
        self.global_promo.name = "16$ on order"
        self.global_promo.discount_type = "fixed_amount"
        self.global_promo.discount_fixed_amount = 16

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
            210,  # 226 - 16
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
        self.assertIn("Discount: 16$", order.order_line[2].name)
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
        self.assertIn("Discount: 16$", order.order_line[2].name)
        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            0,
            2,
            "Promo is not invoiced",
        )
        self.assertAlmostEqual(
            order.order_line[2].qty_delivered,
            1,
            2,
            "Promo is fully delivered",
        )

        invoice = order._create_invoices(final=True).ensure_one()
        invoice.action_post()

        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            1,
            2,
            "Promo is fully invoiced",
        )

        self.assertEqual("Discounted Large Cabinet", invoice.invoice_line_ids[0].name)
        self.assertEqual(
            invoice.invoice_line_ids[0].quantity, 1, "Product has been invoiced"
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_unit, 320, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_total, 160, 2)
        self.assertIn("Conference chair", invoice.invoice_line_ids[1].name)
        self.assertEqual(
            invoice.invoice_line_ids[1].quantity,
            2,
            "Product has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_unit, 16.5, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_total, 33.0, 2)
        self.assertIn("Discount: 16$", invoice.invoice_line_ids[2].name)
        self.assertEqual(
            invoice.invoice_line_ids[2].quantity,
            1,
            "Discount has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[2].price_unit, -16, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[2].price_total, -16, 2)

        backorder = order.picking_ids.filtered(
            lambda p: p.state == "assigned"
        ).ensure_one()
        backorder.move_line_ids[0].qty_done = 1
        res = backorder.button_validate()
        # Create backorder
        Form(self.env[res["res_model"]].with_context(res["context"])).save().process()
        self.assertEqual(len(order.picking_ids), 3)

        invoice = order._create_invoices(final=True).ensure_one()
        invoice.action_post()

        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            1,
            2,
            "Promo is still fully invoiced",
        )
        self.assertEqual(
            len(invoice.invoice_line_ids.filtered(lambda l: "Discount: 16$" in l.name)),
            0,
        )

    def test_sale_coupon_invoice_delivered_invoicing_partial_delivery_specific_products(
        self,
    ):
        self.global_promo.name = "10% on chairs"
        self.global_promo.discount_apply_on = "specific_products"
        self.global_promo.discount_specific_product_ids = [
            (6, 0, [self.conferenceChair.id])
        ]

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
            219.4,  # 226.0 - 0.1 * 4 * 16.5
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
            order.order_line[2].qty_invoiced,
            0,
            2,
            "Promo is not invoiced",
        )
        self.assertAlmostEqual(
            order.order_line[2].qty_delivered,
            0.5,
            2,
            "Promo is therefore partially delivered on specific products",
        )

        invoice = order._create_invoices(final=True).ensure_one()
        invoice.action_post()

        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            0.5,
            2,
            "Promo is now partially invoiced on specific products",
        )

        self.assertEqual("Discounted Large Cabinet", invoice.invoice_line_ids[0].name)
        self.assertEqual(
            invoice.invoice_line_ids[0].quantity, 1, "Product has been invoiced"
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_unit, 320, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_total, 160, 2)
        self.assertIn("Conference chair", invoice.invoice_line_ids[1].name)
        self.assertEqual(
            invoice.invoice_line_ids[1].quantity,
            2,
            "Product has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_unit, 16.5, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_total, 33.0, 2)
        self.assertIn("Discount: 10%", invoice.invoice_line_ids[2].name)
        self.assertEqual(
            invoice.invoice_line_ids[2].quantity,
            0.5,
            "Discount has been partially invoiced on specific products",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[2].price_unit, -6.6, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[2].price_total, -3.3, 2)

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
            order.order_line[2].qty_invoiced,
            0.5,
            2,
            "Promo is partially invoiced on specific products",
        )
        self.assertAlmostEqual(
            order.order_line[2].qty_delivered,
            0.75,
            2,
            "Promo is therefore partially delivered on specific products",
        )

        invoice = order._create_invoices(final=True).ensure_one()
        invoice.action_post()

        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            0.75,
            2,
            "Promo is more partially invoiced on specific products",
        )

        self.assertIn("Conference chair", invoice.invoice_line_ids[0].name)
        self.assertEqual(
            invoice.invoice_line_ids[0].quantity,
            1,
            "Product has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_unit, 16.5, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_total, 16.5, 2)
        self.assertIn("Discount: 10%", invoice.invoice_line_ids[1].name)
        self.assertEqual(
            invoice.invoice_line_ids[1].quantity,
            0.25,
            "Discount has been partially invoiced on specific products",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_unit, -6.6, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_total, -1.65, 2)

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

        invoice = order._create_invoices(final=True).ensure_one()

        invoice.action_post()
        self.assertAlmostEqual(
            order.order_line[2].qty_invoiced,
            1,
            2,
            "Promo is fully invoiced",
        )

        self.assertIn("Conference chair", invoice.invoice_line_ids[0].name)
        self.assertEqual(
            invoice.invoice_line_ids[0].quantity,
            1,
            "Product has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_unit, 16.5, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[0].price_total, 16.5, 2)
        self.assertIn("Discount: 10%", invoice.invoice_line_ids[1].name)
        self.assertEqual(
            invoice.invoice_line_ids[1].quantity,
            0.25,
            "Discount has been partially invoiced",
        )
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_unit, -6.6, 2)
        self.assertAlmostEqual(invoice.invoice_line_ids[1].price_total, -1.65, 2)
