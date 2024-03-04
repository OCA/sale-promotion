# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    _order = "sequence,id"

    chainable = fields.Boolean(
        "Chainable",
        default=False,
        help="Allow this program to chain with previous discounts.",
    )

    rule_minimum_amount_chained = fields.Boolean(
        "Minimum on Chained",
        default=False,
        help="The minimum amount is computed on the previous discounted amount.",
    )


class SaleCouponApplyCode(models.TransientModel):
    _inherit = "sale.coupon.apply.code"

    def process_coupon(self):
        # Force a global recompute since orders can be chainable
        order = self.env["sale.order"].browse(self.env.context.get("active_id"))
        super().process_coupon()
        order.recompute_coupon_lines()
