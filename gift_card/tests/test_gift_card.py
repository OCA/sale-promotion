# Copyright (C) 2021 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from freezegun import freeze_time

from odoo import exceptions, fields

from .common import TestGiftCardCommon


class TestGiftCard(TestGiftCardCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.payment_wizard = cls.env["account.payment.register"]
        cls.so1.action_confirm()
        cls.invoice = cls._confirm_and_invoice_sale(cls, cls.so1)
        ctx = {"active_model": "account.move", "active_ids": [cls.invoice.id]}

        cls.gift_card_wiz = cls.payment_wizard.with_context(ctx).create({})
        cls.gift_card_wiz.button_is_gift_card_payment()

    def _add_gift_card_1(self, amount):
        self.gift_card_wiz.gift_card_code = self.gc1.code
        self.gift_card_wiz.button_add_gift_card_from_code()
        self.gift_card_wiz.gift_card_ids[0].gc_amount_used = amount

    def test_0_create_giftcard(self):
        self.assertEqual(
            len(
                self.env["gift.card"].search([("sale_id", "=", self.so_gift_cards.id)])
            ),
            2,
        )
        self.assertEqual(self.gc1.beneficiary_id, self.partner_1)

    def test_1_gift_card_validation_by_code(self):
        self._add_gift_card_1(50)
        self.gift_card_wiz.action_create_payments()

        self.assertEqual(len(self.gift_card_wiz.gift_card_ids), 1)
        self.assertEqual(self.gift_card_wiz.gift_card_ids[0].gift_card_id, self.gc1)

        self.gift_card_wiz.gift_card_code = "blabla"

        with self.assertRaises(exceptions.UserError) as exc:
            self.gift_card_wiz.button_add_gift_card_from_code()
        self.assertEqual(exc.exception.name, ("The Gift Card Code is invalid."))

        self.assertEqual(len(self.gc1.gift_card_line_ids), 1)
        self.assertEqual(self.gc1.gift_card_line_ids[0].amount_used, 50)
        self.assertEqual(self.gc1.gift_card_line_ids[0].validation_mode, "code")
        payment = self.gc1.gift_card_line_ids[0].payment_id
        self.assertEqual(payment.state, "posted")
        self.assertEqual(payment.amount, 50)
        self.assertRecordValues(
            payment.line_ids,
            [
                {
                    "journal_id": self.gift_card_journal.id,
                    "debit": 50.0,
                    "credit": 0.0,
                },
                {
                    "journal_id": self.gift_card_journal.id,
                    "debit": 0.0,
                    "credit": 50.0,
                },
            ],
        )

    def test_2_gift_card_validation_by_partner(self):
        self.user = self.gc1.beneficiary_id
        self.gift_card_wiz.gift_card_selected_id = self.gc1
        self.gift_card_wiz.button_add_gift_card_from_partner()
        self.gift_card_wiz.gift_card_ids[0].gc_amount_used = 40
        self.gift_card_wiz.action_create_payments()
        self.assertEqual(len(self.gift_card_wiz.gift_card_ids), 1)
        self.assertEqual(self.gift_card_wiz.gift_card_ids[0].gift_card_id, self.gc1)
        self.assertEqual(len(self.gc1.gift_card_line_ids), 1)
        self.assertEqual(self.gc1.gift_card_line_ids[0].amount_used, 40)
        self.assertEqual(self.gc1.gift_card_line_ids[0].validation_mode, "partner")
        payment = self.gc1.gift_card_line_ids[0].payment_id
        self.assertEqual(payment.state, "posted")
        self.assertEqual(payment.amount, 40)
        self.assertRecordValues(
            payment.line_ids,
            [
                {
                    "journal_id": self.gift_card_journal.id,
                    "debit": 40.0,
                    "credit": 0.0,
                },
                {
                    "journal_id": self.gift_card_journal.id,
                    "debit": 0.0,
                    "credit": 40.0,
                },
            ],
        )

    def test_3_gift_card_payment_with_gift_card(self):
        self.gift_card_wiz.button_is_gift_card_payment()

        with self.assertRaises(exceptions.UserError) as exc:
            self.gift_card_wiz.action_create_payments()
        self.assertEqual(exc.exception.name, ("No Gift Card selected."))

    def test_4_sequable_gift_card(self):
        self._add_gift_card_1(10)
        self.gift_card_wiz.action_create_payments()

        self.so2.action_confirm()
        invoice = self._confirm_and_invoice_sale(self.so2)
        ctx = {"active_model": "account.move", "active_ids": [invoice.id]}
        gift_card_wiz2 = self.payment_wizard.with_context(ctx).create({})
        gift_card_wiz2.button_is_gift_card_payment()

        gift_card_wiz2.gift_card_code = self.gc1.code
        gift_card_wiz2.button_add_gift_card_from_code()
        gift_card_wiz2.gift_card_ids[0].gc_amount_used = 25
        gift_card_wiz2.action_create_payments()

        self.assertEqual(len(self.gc1.gift_card_line_ids), 2)
        self.assertEqual(self.gc1.available_amount, 65)

    def test_5_not_sequable_gift_card(self):
        self.gc1.is_divisible = False
        self._add_gift_card_1(15)
        self.gift_card_wiz.with_context(
            test_queue_job_no_delay=True
        ).action_create_payments()

        self.assertEqual(self.gc1.is_divisible, False)
        self.assertEqual(self.gc1.gift_card_line_ids[0].amount_used, 100)
        self.assertEqual(self.gc1.available_amount, 0)
        self.assertEqual(self.gc1.state, "soldout")

    def test_6_gift_card_available_amount_exceptions(self):
        with self.assertRaises(exceptions.UserError) as exc:
            self._add_gift_card_1(-150)
            self.gift_card_wiz.action_create_payments()
        self.assertEqual(
            exc.exception.name, ("The proposed Gift Card amount must be positive.")
        )

        with self.assertRaises(exceptions.UserError) as exc:
            self._add_gift_card_1(150)

        self.assertEqual(
            exc.exception.name,
            (
                "The available amount from the Gift Card '{}' is {}. "
                "The amount proposed must be less than that."
            ).format(self.gc1.name, self.gc1.available_amount),
        )

    @freeze_time("2121-11-10 01:00:00")
    def test_7_inactive_giftcard_if_limited_date(self):
        self.gc1.write({"duration": 10})
        self.assertEqual(self.gc1.state, "outdated")
        with self.assertRaises(exceptions.UserError) as exc:
            self._add_gift_card_1(10)
        self.assertEqual(exc.exception.name, ("The Gift Card is no longer available."))

    def test_8_inactive_giftcard_when_no_available_amount(self):
        self._add_gift_card_1(100)
        self.gift_card_wiz.with_context(
            test_queue_job_no_delay=True
        ).action_create_payments()
        self.assertEqual(self.gc1.available_amount, 0)
        self.assertEqual(self.gc1.state, "soldout")

        with self.assertRaises(exceptions.UserError) as exc:
            self._add_gift_card_1(1)
        self.assertEqual(
            exc.exception.name,
            ("The Gift Card was fully used, no more available amount."),
        )

    def test_9_multiple_gift_card_on_a_payment(self):
        self._add_gift_card_1(10)
        self.gift_card_wiz.gift_card_code = self.gc2.code
        self.gift_card_wiz.button_add_gift_card_from_code()
        self.gift_card_wiz.gift_card_ids[1].gc_amount_used = 20

        self.gift_card_wiz.action_create_payments()

        payment = self.gc1.gift_card_line_ids[0].payment_id
        self.assertEqual(payment.state, "posted")
        self.assertEqual(payment.amount, 30)
        self.assertRecordValues(
            payment.line_ids,
            [
                {
                    "journal_id": self.gift_card_journal.id,
                    "debit": 30.0,
                    "credit": 0.0,
                },
                {
                    "journal_id": self.gift_card_journal.id,
                    "debit": 0.0,
                    "credit": 30.0,
                },
            ],
        )

    def test_10_gift_card_buyer_and_beneficiary(self):
        self.assertEqual(self.gc1.buyer_id, self.gc1.beneficiary_id)
        gc3 = self.gc1.copy({"beneficiary_id": self.partner_2.id})
        self.assertEqual(gc3.buyer_id, self.partner_1)
        self.assertEqual(gc3.beneficiary_id, self.partner_2)

    def test_11_custom_start_date_activation(self):
        gc4 = self.gc1.copy({"start_date": fields.Date.today() + timedelta(days=2)})
        self.assertEqual(gc4.state, "not_activated")

    def test_12_invoice_amount(self):
        self.assertEqual(self.so1.amount_total, 180)
        self._add_gift_card_1(60)
        self.gift_card_wiz.action_create_payments()
        self.assertEqual(self.invoice.amount_total, 180)
        self.assertEqual(self.invoice.amount_residual, 120)
