# Copyright 2024 (APSL-Nagarro) - Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    duration_days = fields.Integer()
