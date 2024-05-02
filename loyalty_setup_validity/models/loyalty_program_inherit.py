# Copyright 2024 Moka Tourisme (https://www.mokatourisme.fr/).
# @author Damien Horvat <ultrarushgame@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from datetime import timedelta


class LoyaltyProgram(models.Model):
    _inherit = 'loyalty.program'

    VALIDITY_TYPE_SELECTION = [
        ('fixed', 'Fixed Date'),
        ('after_activation', 'After Activation'),
    ]

    validity_type = fields.Selection(
        VALIDITY_TYPE_SELECTION, 
        default='fixed', 
        string='Validity Type', 
        required=True,
    )

    validity_duration = fields.Integer(
        string='Validity Duration (days)', 
        default=30
    )

    @api.depends('program_type', 'validity_type')
    def _compute_from_program_type(self):
        super(LoyaltyProgram, self)._compute_from_program_type()
        
        for program in self:
            if program.validity_type == 'fixed':
                program.date_to = fields.Date.today()
            else:
                program.date_to = fields.Date.today() + timedelta(days=program.validity_duration)
