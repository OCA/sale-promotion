# Copyright (C) 2021 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super().action_post()
        for move in self:
            move._create_gift_card()
        return res

    def _create_gift_card(self):
        for sale in self.invoice_line_ids.mapped("sale_line_ids").mapped("order_id"):
            for line in sale.order_line:
                tmpl = line.product_id.product_tmpl_id.gift_cart_template_ids
                if tmpl:
                    i = 0
                    while i < int(line.product_uom_qty):
                        self.env["gift.card"].create(
                            {
                                "sale_id": sale.id,
                                "initial_amount": line.price_unit,
                                "is_divisible": tmpl.is_divisible,
                                "duration": tmpl.duration,
                                "buyer_id": sale.partner_id.id,
                                "gift_card_tmpl_id": tmpl.id,
                            }
                        )
                        i += 1
