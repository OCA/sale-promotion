# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _build_gift_card(self):
        gift_card = super()._build_gift_card()
        print("YOUHOU")
        gift_card['limited_to_product_id'] = self.product_template_id.limited_to_product_id.id
        return gift_card
