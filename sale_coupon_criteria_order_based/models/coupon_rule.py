# Copyright 2022 Ooops404
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleCouponRule(models.Model):
    _inherit = "sale.coupon.rule"

    rule_order_domain = fields.Char(
        string="Based on Order",
        help="Coupon program will work for the order with selected domain only",
    )
