# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class Coupon(models.Model):
    _inherit = "coupon.coupon"

    unconfirmed_sales_order_ids = fields.Many2many(
        "sale.order",
        help="The unconfirmed sales orders that may use this coupon",
        readonly=True,
    )

    def _check_coupon_code(self, order):
        message = super()._check_coupon_code(order)
        if message:
            return message
        if self.program_id in order.unconfirmed_applied_coupon_ids.mapped("program_id"):
            return {"error": _("A Coupon is already applied for the same reward")}
        return message
