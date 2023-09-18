# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    loyalty_program_id = fields.Many2one(
        comodel_name="loyalty.program",
        string="Loyalty Program",
    )

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res["loyalty_program_id"] = "l.loyalty_program_id"
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += """, l.loyalty_program_id"""
        return res
