# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    auto_refresh_coupon = fields.Boolean(
        string="Auto Refresh Coupons",
        help="Autorefresh coupon lines in the backorder",
    )
