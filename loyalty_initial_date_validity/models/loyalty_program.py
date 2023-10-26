# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    date_from = fields.Date(
        string="Start Date",
        help="The start date is included in the validity period of this program",
    )
    # Overwrite field to modify the string and add help
    date_to = fields.Date(
        string="End date",
        help="The end date is included in the validity period of this program",
    )

    @api.constrains("date_from", "date_to")
    def _check_date_from_date_to(self):
        if any(p.date_to and p.date_from and p.date_from > p.date_to for p in self):
            raise UserError(
                _(
                    "The validity period's start date must be anterior or equal to its "
                    "end date."
                )
            )
