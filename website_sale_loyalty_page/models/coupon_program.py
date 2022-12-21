# Copyright 2021 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class CouponProgram(models.Model):
    _name = "coupon.program"
    _inherit = ["coupon.program", "image.mixin", "website.published.mixin"]
    _description = "Coupon display on a website"

    public_name = fields.Html(
        help="Name of the promo showed on website bellow the banner image.",
    )
