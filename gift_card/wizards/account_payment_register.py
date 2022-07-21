# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountGiftCardPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"
    _description = "Register Payment Gift Card"

    is_gift_card_payment = fields.Boolean(
        default=False, string="Payment with Gift Card"
    )

    def button_is_gift_card_payment(self):
        if not self.is_gift_card_payment:
            self.is_gift_card_payment = True
            self.journal_id = self.env.ref("gift_card.gift_card_journal")
        return self._reopen_wizard()

    gift_card_ids = fields.One2many(
        comodel_name="gift.card.selected.wizard", inverse_name="wizard_id"
    )

    gift_card_code = fields.Char(string="Gift Card Code")
    gift_card_selected_id = fields.Many2one(
        "gift.card", domain="[('id', 'not in', self.gift_card_ids.gift_card_id)]"
    )

    gift_card_amount_total = fields.Monetary(
        compute="_compute_gift_card_amount_total", readonly=True
    )

    @api.depends("gift_card_ids", "gift_card_ids.gc_amount_used")
    def _compute_gift_card_amount_total(self):
        for rec in self:
            card_amount_total = 0
            for card in rec.gift_card_ids:
                card_amount_total += card.gc_amount_used
            rec.gift_card_amount_total = card_amount_total
            rec.amount = rec.gift_card_amount_total

    def add_gift_card_payment(self, card):
        validation = "partner"
        if self._context.get("from_code", False):
            validation = "code"

        new_gc = self.env["gift.card.selected.wizard"].create(
            {
                "gift_card_id": card.id,
                "validation_mode": validation,
            }
        )

        self.write({"gift_card_ids": [(4, new_gc.id)]})

    def button_add_gift_card_from_code(self):
        giftcard = self.env["gift.card"]
        if giftcard.check_gift_card_code(self.gift_card_code):
            card = giftcard.search([("code", "=", self.gift_card_code)])
            self.with_context(from_code=True).add_gift_card_payment(card)
            self.gift_card_code = None
        return self._reopen_wizard()

    def button_add_gift_card_from_partner(self):
        if self.gift_card_selected_id:
            if self.gift_card_selected_id.check_gift_card_partner(self.partner_id):
                self.with_context(from_code=False).add_gift_card_payment(
                    self.gift_card_selected_id
                )
                self.gift_card_selected_id = None
                return self._reopen_wizard()
        else:
            raise UserError(_("No Gift Card selected"))

    def _reopen_wizard(self):
        return {
            "name": _("Register Payment"),
            "type": "ir.actions.act_window",
            "res_model": "account.payment.register",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_model": "account.move",
                "active_ids": self.ids,
            },
        }

    def action_create_payments(self):
        if self.is_gift_card_payment and not self.gift_card_ids:
            raise UserError(_("No Gift Card selected."))
        else:
            return super().action_create_payments()

    def _create_payments(self):
        res = super()._create_payments()
        if self.gift_card_ids:
            for card in self.gift_card_ids:
                card.gift_card_id.write(
                    {
                        "gift_card_line_ids": [
                            (
                                0,
                                0,
                                {
                                    "gift_card_id": card.gift_card_id.id,
                                    "payment_id": res.id,
                                    "amount_used": card.gc_amount_used,
                                    "validation_mode": card.validation_mode,
                                },
                            )
                        ]
                    }
                )
        return res

    def _create_payment_vals_from_wizard(self):
        res = super()._create_payment_vals_from_wizard()
        if self.gift_card_ids:
            res["amount"] = self.gift_card_amount_total
        return res


class GiftcardsSelectedWizard(models.TransientModel):
    _name = "gift.card.selected.wizard"
    _description = "Gift cards Wizard"

    gift_card_id = fields.Many2one("gift.card", readonly=True)
    wizard_id = fields.Many2one("account.payment.register")
    gc_name = fields.Char(string="Gift Card ", related="gift_card_id.name")
    gc_amount_available = fields.Monetary(
        string="Available Amount", related="gift_card_id.available_amount"
    )
    gc_amount_used = fields.Monetary(
        string="Amount to use",
        compute="_compute_amount_used",
        inverse="_inverse_amount_used",
        store=True,
    )
    currency_id = fields.Many2one(related="gift_card_id.currency_id")
    validation_mode = fields.Selection(
        [("partner", "By partner"), ("code", "By code")],
    )

    @api.depends("gift_card_id.is_divisible")
    def _compute_amount_used(self):
        for rec in self:
            if not rec.gift_card_id.is_divisible:
                rec.gc_amount_used = rec.gift_card_id.initial_amount

    def _inverse_amount_used(self):
        self._compute_amount_used()

    @api.constrains("gc_amount_used")
    def check_amount(self):
        for line in self:
            if line.gift_card_id.state == "active":
                if line.gc_amount_used < 0:
                    raise UserError(
                        _("The proposed Gift Card amount must be positive.")
                    )
                if line.gc_amount_used > line.gc_amount_available:
                    raise UserError(
                        _(
                            "The available amount from the Gift Card '{}' is {}. "
                            "The amount proposed must be less than that."
                        ).format(line.gift_card_id.name, line.gc_amount_available)
                    )
