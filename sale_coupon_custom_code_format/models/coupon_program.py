# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    custom_code = fields.Boolean(
        string="Custom Code", default=True, help="Use a custom code for this coupon."
    )
    custom_code_mask = fields.Char(
        string="Code Mask",
        default="XXXXXX-00",
        help="The mask used to generate the coupon code.\n"
        "X means a random uppercase letter\n"
        "x means a random lowercase letter\n"
        "0 means a random digit",
    )
    custom_code_forbidden_characters = fields.Char(
        string="Forbidden Characters",
        default="iI1oO0",
        help="The characters that will not be used to generate the coupon code.",
    )
