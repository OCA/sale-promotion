# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    def _get_discount_domain_product_ids(self, order):
        products = super()._get_discount_domain_product_ids(order)
        if order.active_programs_ids:
            products |= order.active_programs_ids.mapped("discount_line_product_id")

        return products
