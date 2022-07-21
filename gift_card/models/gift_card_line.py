# Copyright (C) 2021 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class GiftCardLine(models.Model):
    _name = "gift.card.line"
    _description = "link between giftcard and payments"
    _rec_name = "name"

    name = fields.Char(readonly=True)
    gift_card_id = fields.Many2one(comodel_name="gift.card", readonly=True)
    payment_id = fields.Many2one(comodel_name="account.payment", readonly=True)
    amount_used = fields.Float("Amount", readonly=True)
    validation_mode = fields.Selection(
        [
            ("partner", "By partner"),
            ("code", "By code"),
            ("not_validated", "Not Validated"),
        ],
        string="Validation",
        required=False,
        readonly=True,
        default="not_validated",
        store=True,
    )

    beneficiary_id = fields.Many2one(
        "res.partner",
        string="Gift Card Beneficiary",
        readonly=True,
    )
    code = fields.Char()

    @api.constrains("beneficiary_id", "code")
    def check_gift_card_validity(self):
        giftcard = self.env["gift.card"]
        for rec in self:
            if rec.code:
                giftcard.check_gift_card_code(rec.code)
                rec.validation_mode = "code"
            elif not rec.code:
                rec.gift_card_id.check_gift_card_partner(rec.beneficiary_id)
                rec.validation_mode = "partner"
            else:
                raise UserError(
                    _("The Gift Card '{}' validation failed").format(rec.name)
                )

    @api.constrains("amount_used")
    def check_amount(self):
        for line in self:
            if line.gift_card_id.state == "active":
                if line.amount_used < 0:
                    raise UserError(
                        _("The proposed Gift Card amount must be positive.")
                    )
                if line.gift_card_id.available_amount < 0:
                    raise UserError(
                        _(
                            "The available amount from the Gift Card '{}' is {}. "
                            "The amount proposed must be less than that."
                        ).format(
                            line.gift_card_id.name,
                            line.gift_card_id.available_amount + line.amount_used,
                        )
                    )
