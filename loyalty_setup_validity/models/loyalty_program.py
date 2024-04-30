# Copyright 2024 Moka Tourisme (https://www.mokatourisme.fr/).
# @author Damien Horvat <ultrarushgame@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    VALIDITY_TYPE_SELECTION = [
        ("fixed", "Fixed Date"),
        ("after_activation", "After Activation"),
    ]

    validity_type = fields.Selection(
        VALIDITY_TYPE_SELECTION,
        default="fixed",
        required=True,
    )

    validity_duration = fields.Integer(string="Validity Duration (days)", default=30)
