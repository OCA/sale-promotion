# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MailingMailing(models.Model):
    _inherit = "mailing.mailing"

    rule_id = fields.Many2one(
        comodel_name="loyalty.rule", string="Rule", ondelete="cascade"
    )
