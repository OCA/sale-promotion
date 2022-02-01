# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleCouponProgram(models.Model):
    _name = "sale.coupon.program"
    _inherit = ["sale.coupon.program", "mail.thread", "mail.activity.mixin"]
