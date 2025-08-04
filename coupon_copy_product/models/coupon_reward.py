# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CouponReward(models.Model):
    _inherit = "coupon.reward"

    discount_line_product_id = fields.Many2one(
        copy=True,
    )
