# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _pay_with_gift_card(self, gift_card):
        error = False

        if not gift_card.can_be_used():
            error = _('Invalid or Expired Gift Card.')
        elif gift_card in self.order_line.mapped("gift_card_id"):
            error = _('Gift Card already used.')
        elif gift_card.partner_id and gift_card.partner_id != self.env.user.partner_id:
            error = _('Gift Card are restricted for another user.')
        elif gift_card.limited_to_product_id not in self.order_line.mapped('product_id.product_tmpl_id'):
            error = _('Gift Card restricted to specific product.')

        amount = min(self.amount_total, gift_card.balance_converted(self.currency_id))
        if not error and amount > 0:
            pay_gift_card_id = self.env.ref('gift_card.pay_with_gift_card_product')
            gift_card.redeem_line_ids.filtered(lambda redeem: redeem.state != "sale").unlink()
            self.env["sale.order.line"].create({
                'product_id': pay_gift_card_id.id,
                'price_unit': - amount,
                'product_uom_qty': 1,
                'product_uom': pay_gift_card_id.uom_id.id,
                'gift_card_id': gift_card.id,
                'order_id': self.id
            })
        return error