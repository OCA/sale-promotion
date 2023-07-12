# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class LoyaltyProgram(models.Model):
    _name = "loyalty.program"
    _inherit = ["loyalty.program", "mail.thread", "mail.activity.mixin"]
