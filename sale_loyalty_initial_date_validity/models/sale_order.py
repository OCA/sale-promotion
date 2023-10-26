# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_program_domain(self):
        res = super()._get_program_domain()
        return expression.AND(
            [
                res,
                [
                    "|",
                    ("date_from", "=", False),
                    ("date_from", "<=", fields.Date.context_today(self)),
                ],
            ]
        )

    def _get_trigger_domain(self):
        res = super()._get_trigger_domain()
        return expression.AND(
            [
                res,
                [
                    "|",
                    ("program_id.date_from", "=", False),
                    ("program_id.date_from", "<=", fields.Date.context_today(self)),
                ],
            ]
        )
