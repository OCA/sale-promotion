# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from dateutil.relativedelta import relativedelta
from odoo import fields, models


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def _build_gift_card(self):
        gift_card = super()._build_gift_card()
        gift_card['limited_to_product_id'] = self.product_id.product_tmpl_id.limited_to_product_id.id
        return gift_card