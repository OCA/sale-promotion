# Copyright (C) 2021 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import SavepointCase


class TestGiftCardCommon(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.env.user.tz = "Europe/Paris"
        cls.company = cls.env.ref("base.main_company")

        cls.account_sale = cls.env["account.account"].create(
            {
                "code": "TEST-SALE",
                "name": "Sale - Test",
                "user_type_id": cls.env.ref(
                    "account.data_account_type_direct_costs"
                ).id,
                "company_id": cls.company.id,
            }
        )

        cls.sale_journal = cls.env["account.journal"].create(
            {
                "name": "Sale Journal - Test",
                "code": "SALE",
                "type": "sale",
                "company_id": cls.company.id,
                "default_account_id": cls.account_sale.id,
                "payment_debit_account_id": cls.account_sale.id,
                "payment_credit_account_id": cls.account_sale.id,
            }
        )

        cls.tax = cls.env["account.tax"].create(
            {
                "name": "Tax 20",
                "type_tax_use": "sale",
                "amount": 20,
            }
        )

        cls.tax0 = cls.env["account.tax"].create(
            {
                "name": "Tax 0",
                "type_tax_use": "sale",
                "amount": 0,
            }
        )

        cls.partner_1 = cls.env["res.partner"].create(
            {
                "name": "Test 1",
                "company_id": cls.company.id,
            }
        )
        cls.partner_2 = cls.env["res.partner"].create(
            {
                "name": "Test 2",
                "company_id": cls.company.id,
            }
        )
        cls.gift_card_journal = cls.env.ref("gift_card.gift_card_journal")

        cls.gift_card_account = cls.env["account.account"].create(
            {
                "code": "gift",
                "name": "gift_card_account",
                "user_type_id": cls.env.ref("account.data_account_type_expenses").id,
            }
        )

        cls.template_gift_card = cls.env.ref("gift_card.product_gift_card")

        cls.template_gift_card.write(
            {
                "property_account_income_id": cls.gift_card_account.id,
                "property_account_expense_id": cls.gift_card_account.id,
            }
        )

        cls.product_gift_card = cls.template_gift_card.product_variant_ids[0]
        cls.product_gift_card2 = cls.template_gift_card.product_variant_ids[0]

        cls.product_1 = cls.env["product.product"].create(
            {
                "name": "Product 1",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
            }
        )

        cls.so_gift_cards = cls.env["sale.order"].create(
            {
                "name": "so_gift_cards",
                "partner_id": cls.partner_1.id,
                "partner_shipping_id": cls.partner_1.id,
                "partner_invoice_id": cls.partner_1.id,
            }
        )
        cls.order_line_1 = cls.env["sale.order.line"].create(
            {
                "order_id": cls.so_gift_cards.id,
                "product_id": cls.product_gift_card.id,
                "product_uom": cls.product_1.uom_id.id,
                "product_uom_qty": 1.0,
                "price_unit": 100.0,
                "tax_id": cls.tax0,
            }
        )
        cls.order_line_2 = cls.env["sale.order.line"].create(
            {
                "order_id": cls.so_gift_cards.id,
                "product_id": cls.product_gift_card2.id,
                "product_uom": cls.product_1.uom_id.id,
                "product_uom_qty": 1.0,
                "price_unit": 200.0,
                "tax_id": cls.tax0,
            }
        )
        cls.order_line_3 = cls.env["sale.order.line"].create(
            {
                "order_id": cls.so_gift_cards.id,
                "product_id": cls.product_1.id,
                "product_uom": cls.product_1.uom_id.id,
                "product_uom_qty": 1.0,
                "price_unit": 80.0,
                "tax_id": cls.tax,
            }
        )
        cls.so_gift_cards.action_confirm()

        cls.so1 = cls.env["sale.order"].create(
            {"partner_id": cls.partner_1.id, "name": "so1"}
        )
        cls.order1_line_1 = cls.env["sale.order.line"].create(
            {
                "order_id": cls.so1.id,
                "product_id": cls.product_1.id,
                "product_uom": cls.product_1.uom_id.id,
                "product_uom_qty": 1.0,
                "price_unit": 150.0,
                "tax_id": cls.tax,
            }
        )

        cls.so2 = cls.env["sale.order"].create(
            {"partner_id": cls.partner_1.id, "name": "so2"}
        )
        cls.order2_line_1 = cls.env["sale.order.line"].create(
            {
                "order_id": cls.so2.id,
                "product_id": cls.product_1.id,
                "product_uom": cls.product_1.uom_id.id,
                "product_uom_qty": 1.0,
                "price_unit": 200.0,
                "tax_id": cls.tax,
            }
        )

        for line in cls.so_gift_cards.order_line:
            line.write({"qty_delivered": line.product_uom_qty})
        cls.invoice = cls.so_gift_cards._create_invoices()
        cls.invoice.action_post()

        ctx = {"active_model": "account.move", "active_ids": [cls.invoice.id]}
        cls.payment_model_reg = cls.env["account.payment.register"]
        cls.payment_method_manual_in = cls.env.ref(
            "account.account_payment_method_manual_in"
        )
        register_payments = cls.payment_model_reg.with_context(ctx).create(
            {
                "payment_date": fields.Date.today(),
                "journal_id": cls.sale_journal.id,
                "payment_method_id": cls.payment_method_manual_in.id,
            }
        )
        register_payments._create_payments()
        list_gift_cards = cls.env["gift.card"].search(
            [("sale_id", "=", cls.so_gift_cards.id)]
        )
        cls.gc1, cls.gc2 = list_gift_cards

    def _confirm_and_invoice_sale(self, sale):
        sale.action_confirm()
        for line in sale.order_line:
            line.write({"qty_delivered": line.product_uom_qty})
        invoice = sale._create_invoices()
        invoice.action_post()
        return invoice
