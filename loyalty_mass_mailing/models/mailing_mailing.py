# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MailingMailing(models.Model):
    _inherit = "mailing.mailing"

    program_id = fields.Many2one(
        comodel_name="sale.coupon.program", string="Program", ondelete="cascade"
    )

    @api.onchange("program_id")
    def onchange_program_id(self):
        if self.program_id:
            self.mailing_domain = self.program_id.rule_partners_domain
